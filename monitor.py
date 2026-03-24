import os
import json
import logging
import random
import re
import time
import requests
from urllib.parse import unquote, urlparse, parse_qs
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StateManager:
    def __init__(self, filename="seen_events.json"):
        self.filename = filename
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode {self.filename}, starting fresh.")
        return {"seen_urls": []}

    def is_new(self, url):
        return url not in self.state["seen_urls"]

    def mark_as_seen(self, url):
        if url not in self.state["seen_urls"]:
            self.state["seen_urls"].append(url)

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.state, f, indent=2)
        logger.info(f"State saved to {self.filename}")

class TelegramNotifier:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    def notify(self, platform, url):
        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials missing. Skipping notification.")
            return

        message = (
            f"🚨 NEW RCB EVENT DETECTED ON {platform} 🚨\n"
            f"Link: {url}"
        )
        
        telegram_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(telegram_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Sent Telegram notification for {platform}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

class BaseScraper(ABC):
    KEYWORDS = ["royal-challengers", "rcb", "chinnaswamy", "ipl"]
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]

    def __init__(self):
        self.session = requests.Session()

    def _get_headers(self):
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1"
        }

    def _matches_keywords(self, text):
        if not text:
            return False
        text = text.lower()
        return any(keyword in text for keyword in self.KEYWORDS)

    @abstractmethod
    def scrape(self):
        pass

class BookMyShowScraper(BaseScraper):
    """Monitors BMS indirectly via Google Search to bypass Cloudflare.
    
    BMS uses enterprise Cloudflare protection that blocks all datacenter IPs.
    Instead of fighting the WAF, we search Google for new BMS event pages
    matching our keywords. Google indexes BMS pages within hours.
    """
    PLATFORM = "BookMyShow"
    
    # Multiple Google search queries to cast a wide net
    GOOGLE_QUERIES = [
        'site:in.bookmyshow.com rcb bengaluru ipl 2026',
        'site:in.bookmyshow.com royal challengers bengaluru tickets',
        'site:in.bookmyshow.com chinnaswamy ipl 2026',
    ]
    GOOGLE_URL = "https://www.google.com/search"

    def _google_headers(self):
        """Headers that look like a normal browser doing a Google search."""
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "DNT": "1",
        }

    def _extract_google_urls(self, html):
        """Extract bookmyshow.com URLs from Google search results HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        urls = set()
        
        # Method 1: Standard result links in <a> tags
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Google wraps results in /url?q=<actual_url>&... format
            if '/url?q=' in href:
                parsed = parse_qs(urlparse(href).query)
                actual_url = parsed.get('q', [''])[0]
                if 'bookmyshow.com' in actual_url:
                    urls.add(actual_url)
            elif 'bookmyshow.com' in href and href.startswith('http'):
                urls.add(href)
        
        # Method 2: Look for raw BMS URLs anywhere in the page text
        raw_urls = re.findall(
            r'https?://in\.bookmyshow\.com/[^\s"\'\'<>]+', 
            html
        )
        for url in raw_urls:
            # Clean trailing punctuation
            url = url.rstrip('.,;)]\'"')
            urls.add(url)
        
        return urls

    def _filter_relevant_urls(self, urls):
        """Filter for URLs that contain RCB/IPL keywords (event-specific pages)."""
        relevant = []
        for url in urls:
            url_lower = url.lower()
            # Skip generic/unrelated BMS pages
            if any(skip in url_lower for skip in ['/offers/', '/gift-cards', '/corporates', '/privacy']):
                continue
            # Match keywords in the URL path
            if self._matches_keywords(url_lower):
                relevant.append(url)
            # Also include direct sports event pages (they have event IDs like ET00XXXXXX)
            elif re.search(r'/sports/.*?/ET\d+', url):
                relevant.append(url)
        return relevant

    def scrape(self):
        logger.info(f"Scraping {self.PLATFORM} via Google Search index...")
        all_urls = set()
        
        for query in self.GOOGLE_QUERIES:
            try:
                time.sleep(random.uniform(1, 3))  # Be polite to Google
                resp = self.session.get(
                    self.GOOGLE_URL,
                    params={"q": query, "num": 20, "hl": "en"},
                    headers=self._google_headers(),
                    timeout=15
                )
                resp.raise_for_status()
                found = self._extract_google_urls(resp.text)
                logger.info(f"  Query '{query}': found {len(found)} BMS URLs")
                all_urls.update(found)
            except Exception as e:
                logger.warning(f"Google search failed for '{query}': {e}")
        
        # Filter for actually relevant RCB/IPL event URLs
        relevant = self._filter_relevant_urls(all_urls)
        logger.info(f"  Total relevant BMS URLs: {len(relevant)}")
        return list(set(relevant))

class DistrictScraper(BaseScraper):
    PLATFORM = "District"
    URLS = [
        "https://www.district.in/search?q=rcb",
        "https://www.district.in/search?q=royal+challengers",
    ]

    def scrape(self):
        logger.info(f"Scraping {self.PLATFORM}...")
        all_links = []
        
        for url in self.URLS:
            try:
                response = self.session.get(url, headers=self._get_headers(), timeout=15)
                response.raise_for_status()
                
                # Check Next.js data props
                soup = BeautifulSoup(response.text, 'html.parser')
                next_data_script = soup.find('script', id='__NEXT_DATA__')
                
                if next_data_script:
                    try:
                        data = json.loads(next_data_script.string)
                        # Search through JSON for keywords in any string
                        json_str = json.dumps(data).lower()
                        if any(k in json_str for k in self.KEYWORDS):
                            # If keywords found in JSON, the whole page might be a match
                            # but let's try to extract specific event links if possible
                            # For now, if keywords are in JSON, we'll mark this URL
                            all_links.append(url)
                    except json.JSONDecodeError:
                        pass

                # Fallback to standard <a> tags
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    text = a.get_text()
                    if self._matches_keywords(href) or self._matches_keywords(text):
                        full_url = href if href.startswith('http') else f"https://www.district.in{href}"
                        all_links.append(full_url)

            except requests.exceptions.HTTPError as e:
                logger.warning(f"District blocked request (HTTP {e.response.status_code}) for {url}. Gracefully skipping.")
            except Exception as e:
                logger.error(f"Error scraping District ({url}): {e}")
            
            time.sleep(random.uniform(1, 3)) # Avoid hitting too fast
            
        return list(set(all_links))

class RCBShopScraper(BaseScraper):
    """Monitors the official RCB shop ticket page for ticket availability.
    
    The page at https://shop.royalchallengers.com/ticket is a React SPA.
    We monitor it by:
    1. Scanning the HTML response for ticket/match-related keywords in meta tags,
       inline scripts, and any server-rendered content.
    2. Checking for signs of active ticket listings (e.g., Razorpay checkout 
       integration, match-specific data in inline scripts).
    """
    PLATFORM = "RCB Official Shop"
    URL = "https://shop.royalchallengers.com/ticket"
    
    # Keywords that suggest tickets are actively listed (beyond the static shell)
    TICKET_KEYWORDS = [
        "add to cart", "buy now", "book now", "sold out",
        "match", "vs", "chinnaswamy", "ipl 2026", "ipl 2025",
        "ticket price", "stand", "pavilion", "gallery",
        "select seat", "seat map", "availability",
    ]

    def _check_for_ticket_content(self, html):
        """Check if the page HTML contains indicators of active ticket listings."""
        soup = BeautifulSoup(html, 'html.parser')
        indicators = []
        
        # Check meta tags for ticket-specific content
        for meta in soup.find_all('meta'):
            content = meta.get('content', '')
            if any(kw in content.lower() for kw in self.TICKET_KEYWORDS):
                indicators.append(f"Meta tag: {content[:100]}")
        
        # Check for inline script data (SPAs often embed initial state)
        for script in soup.find_all('script'):
            if script.string:
                script_text = script.string.lower()
                for kw in self.TICKET_KEYWORDS:
                    if kw in script_text:
                        indicators.append(f"Script contains: '{kw}'")
                        break
        
        # Check page title changes (might update when tickets are live)
        title = soup.find('title')
        if title and title.string:
            title_text = title.string.lower()
            if any(kw in title_text for kw in ['ticket', 'match', 'book', 'ipl']):
                indicators.append(f"Title: {title.string}")
        
        # Check if there are significantly more DOM elements than the bare shell
        # The empty SPA shell has very few elements in <body>
        body = soup.find('body')
        if body:
            all_elements = body.find_all()
            # An active ticket page would have many more rendered elements
            # The bare shell only has noscript + div#rcb-shop
            if len(all_elements) > 10:
                indicators.append(f"Body has {len(all_elements)} elements (possible SSR content)")
        
        return indicators

    def scrape(self):
        logger.info(f"Scraping {self.PLATFORM}...")
        results = []
        
        try:
            response = self.session.get(
                self.URL,
                headers=self._get_headers(),
                timeout=15
            )
            response.raise_for_status()
            
            indicators = self._check_for_ticket_content(response.text)
            
            if indicators:
                logger.info(f"  Ticket indicators found on RCB shop:")
                for ind in indicators:
                    logger.info(f"    - {ind}")
                results.append(self.URL)
            else:
                logger.info(f"  No active ticket indicators on RCB shop (SPA shell only).")
                
        except requests.exceptions.HTTPError as e:
            logger.warning(f"RCB shop returned HTTP {e.response.status_code}. Skipping.")
        except Exception as e:
            logger.error(f"Error scraping RCB shop: {e}")
        
        return results

def main():
    state_manager = StateManager()
    notifier = TelegramNotifier()
    
    scrapers = [
        BookMyShowScraper(),
        DistrictScraper(),
        RCBShopScraper(),
    ]
    
    new_found = False
    
    for scraper in scrapers:
        links = scraper.scrape()
        for link in links:
            if state_manager.is_new(link):
                logger.info(f"NEW EVENT FOUND: {link}")
                notifier.notify(scraper.PLATFORM, link)
                state_manager.mark_as_seen(link)
                new_found = True
            else:
                logger.debug(f"Already seen: {link}")
    
    if new_found:
        logger.info("New event(s) found — saving updated state.")
    else:
        logger.info("No new events found.")
    
    state_manager.save()

if __name__ == "__main__":
    main()
