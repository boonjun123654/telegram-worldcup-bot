import asyncio
import os
import re
import json

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

ADMIN_IDS = {
    7166921660
}


def save_active_match(data):
    with open("active_match.json", "w") as f:
        json.dump(data, f)


def load_active_match():
    try:
        with open("active_match.json", "r") as f:
            return json.load(f)
    except:
        return {}


async def handle_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    text = update.message.text.strip()

    # 开盘
    if text.startswith("/newmatch/"):

        if update.effective_user.id not in ADMIN_IDS:
            return

        try:

            parts = text.split("/")

            match_id = parts[2]
            team1 = parts[3]
            team2 = parts[4]
            team3 = parts[5]

            data = {
                "match_id": match_id,
                "team1": team1,
                "team2": team2,
                "team3": team3,
                "status": "OPEN"
            }

            save_active_match(data)

            await update.message.reply_text(
                f"✅ Match Created\n\n{match_id}\n{team1} vs {team2}"
            )

        except:
            await update.message.reply_text(
                "Format:\n/newmatch/M0001/France/Japan/Seri"
            )

        return

    # 封盘
    if text.startswith("/stopmatch/"):

        if update.effective_user.id not in ADMIN_IDS:
            return

        match = load_active_match()

        if not match:
            await update.message.reply_text(
                "❌ No Active Match"
            )
            return

        match["status"] = "CLOSED"

        save_active_match(match)

        await update.message.reply_text(
            f"⛔ Match Closed\n\n{match['match_id']}"
        )

        return

    # 玩家竞猜
    match_data = load_active_match()

    if not match_data:
        await update.message.reply_text(
            "❌ No Active Match"
        )
        return

    if match_data["status"] != "OPEN":
        await update.message.reply_text(
            "❌ Prediction Closed"
        )
        return

    pattern = r"win\s*:\s*(.+)\njumlah\s*gol\s*:\s*(.+)"

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

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


async def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT,
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
