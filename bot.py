import os
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from datetime import datetime

# ── KEYS ───────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", "5373827517"))

# ── GOOGLE SHEETS SETUP ────────────────────────────────
SHEET_ID = "1YFZKjEzYenJK8ZnIAmvOuvXhwNYOZ6Q6rKJNmfjLVjQ"
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).sheet1

# ── OPENROUTER SETUP ───────────────────────────────────
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ── RESTAURANT INFO ────────────────────────────────────
RESTAURANT_INFO = """
You are a helpful AI assistant for a restaurant called "Sakil's Kitchen".

MENU:
- Burger: ₩8,000
- Pasta: ₩12,000
- Pizza: ₩15,000
- Coffee: ₩4,000
- Juice: ₩3,500

OPENING HOURS:
Monday to Saturday: 10am to 10pm
Sunday: Closed

LOCATION:
Busan, South Korea

RESERVATION INSTRUCTIONS:
When a customer wants to make a reservation, collect ALL of this information one by one:
1. Full name
2. Date
3. Time
4. Number of people
5. Menu items they want
6. Phone number

Once you have ALL details, confirm by saying:
"✅ RESERVATION CONFIRMED:
Name: [name]
Date: [date]
Time: [time]
People: [number]
Menu: [items]
Phone: [number]"

Always include "RESERVATION CONFIRMED" exactly when confirming.
"""

# ── CONVERSATION MEMORY ────────────────────────────────
conversation_history = {}

# ── HANDLERS ───────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    conversation_history[user_id] = []
    await update.message.reply_text(
        "Hello! 👋 Welcome to Sakil's Kitchen!\n"
        "I can help you with our menu, hours, and reservations.\n"
        "How can I help you today?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_message = update.message.text
    customer_name = update.message.from_user.first_name

    # Initialize conversation history for new users
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # Add user message to history
    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })

    # Build messages with full history
    messages = [{"role": "system", "content": RESTAURANT_INFO}] + conversation_history[user_id]

    # Get AI response
    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=messages
    )

    reply = response.choices[0].message.content

    # Add bot reply to history
    conversation_history[user_id].append({
        "role": "assistant",
        "content": reply
    })

    # Send reply to customer
    await update.message.reply_text(reply)

    # Check if reservation confirmed
    if "RESERVATION CONFIRMED" in reply:
        # Save to Google Sheets
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        sheet.append_row([now, customer_name, user_message, reply])

        # Notify owner
        await context.bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text=f"🎉 NEW RESERVATION!\n\n{reply}\n\n👤 Telegram: {customer_name}"
        )
    else:
        # Regular notification
        await context.bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text=f"📩 New Message!\n\n👤 {customer_name}\n💬 {user_message}\n🤖 {reply}"
        )

# ── RUN BOT ────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()