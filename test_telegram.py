import os
import requests

def test_telegram():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variables are not set.")
        print("Set them using:")
        print("export TELEGRAM_BOT_TOKEN='your_token_here'")
        print("export TELEGRAM_CHAT_ID='your_chat_id_here'")
        return

    print(f"Testing Telegram notification...")
    message = "🔔 *RCB Ticket Bot Test Message*\n\nIf you see this, your bot is correctly configured and can send messages to this group! ✅"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Success! Check your Telegram group/channel.")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    test_telegram()
