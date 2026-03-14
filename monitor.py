import os
import json
import logging
import random
import time
import requests
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
    PLATFORM = "BookMyShow"
    URL = "https://in.bookmyshow.com/explore/sports-bengaluru"

    def scrape(self):
        logger.info(f"Scraping {self.PLATFORM}...")
        try:
            response = self.session.get(self.URL, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []

            # BMS often uses event cards or generic <a> tags
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text()
                
                # Check for keywords in URL or Link text
                if self._matches_keywords(href) or self._matches_keywords(text):
                    # Clean up the URL
                    full_url = href if href.startswith('http') else f"https://in.bookmyshow.com{href}"
                    links.append(full_url)
            
            return list(set(links))
        except requests.exceptions.HTTPError as e:
            logger.warning(f"BMS blocked request (HTTP {e.response.status_code}). Gracefully skipping.")
            return []
        except Exception as e:
            logger.error(f"Error scraping BMS: {e}")
            return []

class DistrictScraper(BaseScraper):
    PLATFORM = "District"
    URLS = [
        "https://www.district.in/search?q=rcb",
        "https://www.district.in/sports"
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

def main():
    state_manager = StateManager()
    notifier = TelegramNotifier()
    
    scrapers = [
        BookMyShowScraper(),
        DistrictScraper()
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
        state_manager.save()
    else:
        logger.info("No new events found.")

if __name__ == "__main__":
    main()
