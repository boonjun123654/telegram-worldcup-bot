import os
import re

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def handle_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    text = update.message.text.strip()

    pattern = r"win\s*:\s*(.+)\njumlah\s*gol\s*:\s*(.+)"

    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return

    username = update.effective_user.username

    if username:
        mention = f"@{username}"
    else:
        mention = update.effective_user.first_name

    await update.message.reply_text(
        f"✅ {mention} Prediction Recorded"
    )


def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_prediction
        )
    )

    print("Bot Running...")

    app.run_polling()


if __name__ == "__main__":
    main()
