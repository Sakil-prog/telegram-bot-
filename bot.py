from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
import os 

# ── YOUR KEYS ──────────────────────────────────────────
OPENROUTER_API_KEY =os.getenv("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")
TELEGRAM_TOKEN = os.getenv("8688450695:AAEsKlXZ-SBYa1wgnj_As6Lb7YxNfLhSh0k")

# ── SETUP CLIENT ───────────────────────────────────────
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ── RESTAURANT INFO ────────────────────────────────────
RESTAURANT_INFO = """
You are a helpful AI assistant for a restaurant called "Sakil's Kitchen".
You help customers with:
- Menu questions
- Opening hours: Monday to Saturday, 10am to 10pm
- Reservations
- Location: Busan, South Korea
- Pricing questions

Always be friendly, professional and helpful.
If you don't know something, say "Please contact us directly for more info."
Keep answers short and clear.
"""

# ── HANDLERS ───────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! 👋 Welcome to Sakil's Kitchen!\n"
        "I'm your AI assistant. Ask me anything about our menu, hours, or reservations!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[
            {"role": "system", "content": RESTAURANT_INFO},
            {"role": "user", "content": user_message}
        ]
    )

    await update.message.reply_text(response.choices[0].message.content)

# ── RUN BOT ────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()