# Role & Objective
You are an expert Python backend developer. Write a robust, serverless monitoring script to detect when Royal Challengers Bengaluru (RCB) IPL 2026 match tickets are published on either **BookMyShow** or **District by Zomato**.

# Core Requirements
1. **Target Platforms & URLs to Monitor:**
   - **BookMyShow:** Monitor the Bengaluru sports page (`https://in.bookmyshow.com/explore/sports-bengaluru`). 
   - **District by Zomato:** Monitor the District web platform. Use their search or sports directory (e.g., `https://www.district.in/search?q=rcb` or `https://www.district.in/sports`). You may also need to check the Next.js data props (`__NEXT_DATA__`) in the HTML.

2. **Scraping Strategy (Dual Platform):**
   - Use `requests` and `BeautifulSoup`.
   - Implement aggressive header rotation (rotate standard Chrome/Safari desktop and mobile User-Agents, accept languages, etc.) to avoid basic WAF blocks from Cloudflare/Akamai.
   - For both platforms, look for `<a>` tags, event cards, or JSON data blocks containing any of these keywords: `["royal-challengers", "rcb", "chinnaswamy", "ipl"]`.

3. **State Management (Crucial):**
   - The bot must not spam. It needs to remember which URLs it has already alerted us about.
   - Use a simple local JSON or text file (e.g., `seen_events.json`) to store detected hrefs or event IDs. 
   - When running in GitHub Actions, use actions/cache or commit the file back to the repo to persist the state between cron runs.

4. **Notification System:**
   - Use the Telegram Bot API (`requests.post`).
   - Read `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from environment variables.
   - The message should clearly state the platform: "🚨 NEW RCB EVENT DETECTED ON [BookMyShow/District] 🚨\nLink: <URL>"

5. **Infrastructure / Deployment:**
   - Generate a complete `.github/workflows/monitor.yml` file.
   - Set the cron schedule to run every 5 minutes (`*/5 * * * *`).
   - Ensure the workflow handles the state persistence (committing the updated `seen_events.json` back to the repository so the next run knows what was already found).

# Constraints & Edge Cases
- Handle HTTP 403/429 errors gracefully. If either BMS or District blocks the request, do NOT crash the action. Log it as a warning and exit cleanly so the next cron job can try again.
- Keep dependencies minimal (just `requests` and `beautifulsoup4` in a `requirements.txt`).
- Output clean, production-ready code with basic logging. 
- Ensure the code is modular so I can easily add a new platform later if needed.