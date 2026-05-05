import requests
import os

# --- CONFIGURATION ---
# Set these in your .env or Streamlit Secrets:
#   TELEGRAM_BOT_TOKEN=your_bot_token_from_BotFather
#   TELEGRAM_CHAT_ID=your_personal_chat_id

def get_config():
    """Get Telegram bot token and chat ID from environment."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    return token, chat_id

def send_message(text):
    """Send a message to the admin via Telegram bot."""
    token, chat_id = get_config()
    
    if not token or not chat_id:
        return False  # Telegram not configured, silently skip
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False  # Don't crash the app if Telegram fails

def notify_new_user(username):
    """Notify admin about a new user registration."""
    text = (
        "🆕 <b>New User Registered!</b>\n\n"
        f"👤 Username: <code>{username}</code>\n"
        f"💰 Credits: 10 (free trial)\n\n"
        "Check your Admin Panel for details."
    )
    return send_message(text)

def notify_credits_empty(username):
    """Notify admin when a user runs out of credits."""
    text = (
        "⚠️ <b>User Out of Credits!</b>\n\n"
        f"👤 Username: <code>{username}</code>\n"
        f"💰 Credits: 0\n\n"
        "This user may want to buy more credits. 💸"
    )
    return send_message(text)

def notify_credit_request(username, message):
    """Notify admin about a credit purchase request."""
    text = (
        "💳 <b>Credit Purchase Request!</b>\n\n"
        f"👤 From: <code>{username}</code>\n"
        f"💬 Message: {message}\n\n"
        "Go to Admin Panel to add credits."
    )
    return send_message(text)
