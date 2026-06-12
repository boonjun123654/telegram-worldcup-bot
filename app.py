import asyncio
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

    mention = f"@{username}" if username else update.effective_user.first_name

    await update.message.reply_text(
        f"✅ {mention} Prediction Recorded"
    )


async def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_prediction
        )
    )

    print("Bot Running...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
