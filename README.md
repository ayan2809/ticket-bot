# 🏏 RCB IPL 2026 Ticket Monitor Bot

A serverless, $0-cost monitoring bot that tracks **Royal Challengers Bengaluru (RCB)** IPL 2026 ticket listings across **BookMyShow** and **District by Zomato**. It runs every 5 minutes via GitHub Actions and sends instant alerts to Telegram.

## 🚀 Features

- **Cloudflare Bypass**: Indirectly monitors BookMyShow via the Google Search index to bypass aggressive Cloudflare WAF/403 blocks.
- **District by Zomato Support**: Deep-scrapes District's Next.js metadata to find upcoming matches.
- **Telegram Alerts**: Instant notifications to your private channel or group.
- **Persistent State**: Automatically tracks "seen" events in `seen_events.json` to prevent duplicate alerts.
- **$0 Running Cost**: Utilizing GitHub Actions for public repositories for 100% free automation.

## 🛠 Project Structure

```text
ticket-bot/
├── .github/workflows/monitor.yml  # Automation rules (5-min cron)
├── docs/                          # Detailed docs & cost analysis
├── monitor.py                     # Main bot logic & scraper classes
├── requirements.txt               # Dependencies (requests, bs4)
├── seen_events.json               # Persistent state (auto-updated)
└── test_telegram.py               # Connectivity test utility
```

## ⚙️ Setup Instructions

### 1. Telegram Bot Setup
1. Create a bot with [@BotFather](https://t.me/botfather) and save the API Token.
2. Create a Telegram channel/group and add your bot as an administrator.
3. Get your Chat ID (e.g., `-1003803834413`) by sending a message and checking `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`.

### 2. GitHub Configuration
1. Fork or push this code to your GitHub repository.
2. Go to **Settings > Secrets and variables > Actions**.
3. Add the following **Repository Secrets**:
   - `TELEGRAM_BOT_TOKEN`: Your API token.
   - `TELEGRAM_CHAT_ID`: Your group/channel Chat ID.

### 3. Verification
1. Go to the **Actions** tab in your repo.
2. Select **RCB Ticket Monitor** -> **Run workflow**.
3. Once finished, check your Telegram for a confirmation or potential alerts!

## 🧪 Local Testing

You can test the notification system locally:

```bash
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_id'
python test_telegram.py
```

## 📊 Cost Analysis

| Component | Cost | Why? |
|---|---|---|
| **GitHub Actions** | **$0.00** | Free for public repositories. |
| **Telegram API** | **$0.00** | Free bot API tier. |
| **Scraper Proxy** | **$0.00** | Not needed (uses Google Index bypass). |
| **Total** | **$0.00** | Forever. |

---
*Created with ❤️ for RCB Fans. Go Challengers!* 🏆
