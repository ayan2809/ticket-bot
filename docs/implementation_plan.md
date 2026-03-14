# RCB IPL 2026 Ticket Monitor Bot

A serverless monitoring bot that scrapes BookMyShow and District by Zomato for RCB ticket listings, sends Telegram alerts for new events, and runs every 5 minutes via GitHub Actions.

> [!NOTE]
> This repository will be **public** to take advantage of GitHub Actions' unlimited free minutes for public projects, ensuring a total cost of **$0/month**.

## Proposed Changes

### Dependencies

#### [NEW] [requirements.txt](file:///Volumes/Projects/ticket-bot/requirements.txt)
```
requests
beautifulsoup4
```

---

### Monitoring Script

#### [NEW] [monitor.py](file:///Volumes/Projects/ticket-bot/monitor.py)

Single-file, modular architecture with these classes:

| Class | Responsibility |
|---|---|
| `BaseScraper` | Abstract base with shared HTTP logic, header rotation, keyword matching |
| `BookMyShowScraper` | Scrapes `in.bookmyshow.com/explore/sports-bengaluru` for event links/cards |
| `DistrictScraper` | Scrapes `district.in/search?q=rcb` + `district.in/sports`, also parses `__NEXT_DATA__` JSON |
| `StateManager` | Loads/saves `seen_events.json`, deduplicates URLs |
| `TelegramNotifier` | Posts formatted alerts via Telegram Bot API |

**Key design details:**
- **Header rotation**: Pool of ~10 realistic Chrome/Safari UA strings (desktop + mobile), randomized `Accept-Language`, `Referer`, etc.
- **Keyword matching**: Scans `<a>` tags, event cards, and embedded JSON for `["royal-challengers", "rcb", "chinnaswamy", "ipl"]` (case-insensitive)
- **Error handling**: Catches `requests.exceptions.HTTPError` for 403/429 — logs a warning and continues to the next platform. Never crashes the Action.
- **Logging**: Uses Python `logging` module at INFO level with clean formatting.
- **Entry point**: `if __name__ == "__main__"` block that orchestrates: load state → scrape all platforms → diff → notify → save state.

---

### State Persistence

#### [NEW] [seen_events.json](file:///Volumes/Projects/ticket-bot/seen_events.json)
Empty initial state: `{"seen_urls": []}`. Updated in-place after each run.

---

### GitHub Actions Workflow

#### [NEW] [.github/workflows/monitor.yml](file:///Volumes/Projects/ticket-bot/.github/workflows/monitor.yml)

```yaml
name: RCB Ticket Monitor
on:
  schedule:
    - cron: '*/5 * * * *'
  workflow_dispatch: {}
```

**Steps:**
1. Checkout repo (`git@github.com:ayan2809/ticket-bot.git`)
2. Set up Python 3.13
3. Install dependencies from `requirements.txt`
4. Run `monitor.py` with `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from repository secrets
5. Commit & push updated `seen_events.json` back to repo (using `git diff --quiet` to skip if unchanged)

---

## Verification Plan

### Automated Tests
1. **Syntax & import check**: `python3 -c "import monitor; print('OK')"` — confirms no import/syntax errors
2. **YAML lint**: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/monitor.yml'))"` — validates workflow syntax
3. **Dry-run mode**: Run `python3 monitor.py` without Telegram env vars set — should log warnings about missing credentials but not crash

### Manual Verification
- After pushing to GitHub, add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as repository secrets, then manually trigger the workflow via **Actions → RCB Ticket Monitor → Run workflow** and check Telegram for alerts or the Actions log for clean execution.
