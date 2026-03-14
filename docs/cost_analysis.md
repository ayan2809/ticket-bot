# Cost Analysis — RCB Ticket Monitor Bot

## Summary

| Component | Monthly Cost (Free Tier) | Monthly Cost (Paid) |
|---|---|---|
| GitHub Actions compute | **$0** | ~$1.15 |
| Telegram Bot API | **$0** | **$0** |
| **Total** | **$0/month** | **~$1.15/month** |

> [!TIP]
> For a **public repository**, this bot runs entirely for free on GitHub's Free plan.

---

## 1. GitHub Actions Compute

### Usage Math

| Parameter | Value |
|---|---|
| Cron frequency | Every 5 minutes |
| Runs per hour | 12 |
| Runs per day | 288 |
| Runs per month (30 days) | **8,640** |
| Estimated runtime per run | ~30–45 seconds |
| Total minutes per month | **~4,320–6,480 min** |

### Pricing Tiers

| Scenario | Free Minutes | Overage Rate | Est. Monthly Cost |
|---|---|---|---|
| **Public repo** (any plan) | **Unlimited** | — | **$0** |
| **Private repo** — GitHub Free | 2,000 min/month | $0.008/min (Linux) | ~$19–36 ⚠️ |
| **Private repo** — GitHub Pro | 3,000 min/month | $0.008/min (Linux) | ~$11–28 ⚠️ |

---

## 2. Telegram Bot API

| Item | Cost |
|---|---|
| Bot creation | Free |
| Sending messages | Free (up to ~30 msg/sec) |
| Channel/group messaging | Free |
| No monthly fees | — |

---

## 3. Other Costs

| Item | Cost | Notes |
|---|---|---|
| Domain / hosting | **$0** | No server needed; GitHub Actions handles it |
| State storage | **$0** | `seen_events.json` committed to repo |
| Dependencies | **$0** | `requests` + `beautifulsoup4` are free |

---

## Bottom Line

> [!IMPORTANT]
> **Confirmed Setup: Public Repository**
>
> By keeping the repository public, the total cost for running this bot (GitHub Actions + Telegram API) is **exactly $0.00**.
