# Telegram Bot Setup Guide

This guide covers how to generate the required `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` environment variables for the ticket monitoring bot.

## 1. Generate the TELEGRAM_BOT_TOKEN

The token is your authentication key. Keep this secure and never commit it to public version control.

1. Open Telegram and search for the official **@BotFather** account (look for the verified blue checkmark).
2. Start a chat and send the command: `/newbot`
3. Provide a display name for your bot (e.g., `RCB Ticket Monitor`).
4. Provide a unique username. It must end in `bot` (e.g., `rcb_chinnaswamy_alert_bot`).
5. BotFather will generate a success message containing your **HTTP API Token**. It looks like this: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`.
6. Copy this token. This is your `TELEGRAM_BOT_TOKEN`.

## 2. Set Up the Alert Channel

You need a destination for the bot to send messages. A Telegram Channel is best because you can broadcast to multiple friends.

1. Create a new **New Channel** in Telegram (e.g., "RCB 2026 Alerts").
2. Go to the channel settings and add the bot you just created as an **Administrator**. (It needs admin rights to post messages).
3. Post a single test message in the channel from your personal account (e.g., "Test"). *This step is required to generate an event in the API.*

## 3. Retrieve the TELEGRAM_CHAT_ID

Channels have unique, negative integer IDs. We will hit the Telegram API directly to extract this ID.

1. Open your terminal and run the following `curl` command, replacing `<YOUR_BOT_TOKEN>` with the token from Step 1:

   ```bash
   curl "[https://api.telegram.org/bot](https://api.telegram.org/bot)<YOUR_BOT_TOKEN>/getUpdates"