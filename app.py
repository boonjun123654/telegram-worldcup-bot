import asyncio
import os
import re
import psycopg2

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
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True

ADMIN_IDS = {
    7166921660
}


def get_active_match():

    cur = conn.cursor()

    cur.execute("""
        SELECT match_code, team1, team2, team3, status
        FROM matches
        WHERE status='OPEN'
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cur.fetchone()

    cur.close()

    if not row:
        return None

    return {
        "match_id": row[0],
        "team1": row[1],
        "team2": row[2],
        "team3": row[3],
        "status": row[4]
    }

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.strip()

    # ==========================
    # NEW MATCH
    # ==========================

    if text.startswith("/newmatch/"):

        if update.effective_user.id not in ADMIN_IDS:
            return

        try:

            parts = text.split("/")

            match_id = parts[2]
            team1 = parts[3]
            team2 = parts[4]
            team3 = parts[5]

            cur = conn.cursor()

            # 关闭所有旧比赛
            cur.execute("""
                UPDATE matches
                SET status='CLOSED'
                WHERE status='OPEN'
            """)

            # 创建新比赛
            cur.execute("""
                INSERT INTO matches
                (
                    match_code,
                    team1,
                    team2,
                    team3,
                    status
                )
                VALUES (%s,%s,%s,%s,'OPEN')
            """,
            (
                match_id,
                team1,
                team2,
                team3
            ))

            cur.close()

            await update.message.reply_text(
                f"✅ Perlawanan Dicipta\n\n{match_id}\n{team1} lawan {team2}"
            )

        except Exception as e:

            if "duplicate" in str(e).lower():

                await update.message.reply_text(
                    f"❌ ID Perlawanan Sudah Wujud\n\n{match_id}"
                )

            else:

                await update.message.reply_text(
                    "Format:\n/newmatch/M0001/France/Japan/Seri"
                )

        return
    # ==========================
    # STOP MATCH
    # ==========================

    if text.startswith("/stopmatch/"):

        if update.effective_user.id not in ADMIN_IDS:
            return

        try:

            parts = text.split("/")
            match_id = parts[2]

            cur = conn.cursor()

            cur.execute("""
                UPDATE matches
                SET status='CLOSED'
                WHERE match_code=%s
            """,
            (match_id,))

            cur.close()

            await update.message.reply_text(
                f"⛔ Perlawanan Ditutup\n\n{match_id}"
            )

        except:

            await update.message.reply_text(
                "Format:\n/stopmatch/M0001"
            )

        return

    # ==========================
    # SUMMARY
    # ==========================

    if text.startswith("/summary/"):

        if update.effective_user.id not in ADMIN_IDS:
            return

        try:

            parts = text.split("/")
            match_id = parts[2]

            cur = conn.cursor()

            # 取得比赛资料
            cur.execute("""
                SELECT team1, team2, team3
                FROM matches
                WHERE match_code=%s
            """,
            (match_id,))

            match_row = cur.fetchone()

            if not match_row:

                cur.close()

                await update.message.reply_text(
                    f"❌ Perlawanan Tidak Ditemui\n\n{match_id}"
                )

                return

            team1 = match_row[0]
            team2 = match_row[1]
            team3 = match_row[2]

            # 统计 team1
            cur.execute("""
                SELECT COUNT(*)
                FROM predictions
                WHERE match_code=%s
                AND LOWER(win_choice)=LOWER(%s)
            """,
            (match_id, team1))

            count_team1 = cur.fetchone()[0]

            # 统计 team2
            cur.execute("""
                SELECT COUNT(*)
                FROM predictions
                WHERE match_code=%s
                AND LOWER(win_choice)=LOWER(%s)
            """,
            (match_id, team2))

            count_team2 = cur.fetchone()[0]

            # 统计 Seri
            cur.execute("""
                SELECT COUNT(*)
                FROM predictions
                WHERE match_code=%s
                AND LOWER(win_choice)=LOWER(%s)
            """,
            (match_id, team3))

            count_team3 = cur.fetchone()[0]

            total = (
                count_team1 +
                count_team2 +
                count_team3
            )

            cur.close()

            await update.message.reply_text(
                f"📊 Ringkasan Ramalan\n\n"
                f"Perlawanan : {match_id}\n\n"
                f"{team1} : {count_team1}\n"
                f"{team2} : {count_team2}\n"
                f"{team3} : {count_team3}\n\n"
                f"Jumlah Ramalan : {total}"
            )

        except:

            await update.message.reply_text(
                "Format:\n/summary/M0001"
            )

        return
    # ==========================
    # RESULTS
    # ==========================

    if text.startswith("/results/"):

        if update.effective_user.id not in ADMIN_IDS:
            return

        try:

            parts = text.split("/")

            match_id = parts[2]
            result_win = parts[3]
            result_goal = parts[4]

            cur = conn.cursor()

            cur.execute("""
                UPDATE matches
                SET
                    status='CLOSED',
                    result_win=%s,
                    result_goal=%s
                WHERE match_code=%s
            """,
            (
                result_win,
                result_goal,
                match_id
            ))

            cur.execute("""
                SELECT username
                FROM predictions
                WHERE match_code=%s
                AND LOWER(win_choice)=LOWER(%s)
                AND goal_prediction=%s
            """,
            (
                match_id,
                result_win,
                result_goal
            ))

            rows = cur.fetchall()

            cur.close()

            winners = [row[0] for row in rows]

            if winners:
                winner_text = "\n".join(winners)
            else:
                winner_text = "Tiada Pemenang"

            await update.message.reply_text(
                f"🏆 KEPUTUSAN {match_id}\n\n"
                f"Menang : {result_win}\n"
                f"Jumlah Gol : {result_goal}\n\n"
                f"✅ Peramal Tepat\n\n"
                f"{winner_text}\n\n"
                f"Jumlah Pemenang : {len(winners)}"
            )

        except:

            await update.message.reply_text(
                "Format:\n/results/M0001/France/2"
            )

        return

    # ==========================
    # PLAYER PREDICTION
    # ==========================

    match_data = get_active_match()

    if not match_data:
        return

    pattern = r"(?:menang|win)\s*:\s*(.+)\njumlah\s*gol\s*:\s*(.+)"

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if not match:
        return

    win_choice = match.group(1).strip()
    goal_choice = match.group(2).strip()

    if not goal_choice.isdigit():

        await update.message.reply_text(
            "❌ Jumlah gol mesti nombor"
        )

        return

    allowed = [
        match_data["team1"].lower(),
        match_data["team2"].lower(),
        match_data["team3"].lower()
    ]

    if win_choice.lower() not in allowed:

        await update.message.reply_text(
            f"❌ Pasukan Tidak Sah\n\n"
            f"Pilihan tersedia:\n"
            f"{match_data['team1']}\n"
            f"{match_data['team2']}\n"
            f"{match_data['team3']}"
        )

        return

    username = update.effective_user.username

    if username:
        mention = f"@{username}"
    else:
        mention = update.effective_user.first_name

    user_id = update.effective_user.id

    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM predictions
        WHERE match_code=%s
        AND user_id=%s
    """,
    (
        match_data["match_id"],
        user_id
    ))

    existing = cur.fetchone()

    if existing:

        cur.execute("""
            UPDATE predictions
            SET
                win_choice=%s,
                goal_prediction=%s
            WHERE id=%s
        """,
        (
            win_choice,
            goal_choice,
            existing[0]
        ))

        status_text = "Dikemas Kini"

    else:

        cur.execute("""
            INSERT INTO predictions
            (
                match_code,
                user_id,
                username,
                win_choice,
                goal_prediction
            )
            VALUES (%s,%s,%s,%s,%s)
        """,
        (
            match_data["match_id"],
            user_id,
            mention,
            win_choice,
            goal_choice
        ))

        status_text = "Direkodkan"

    cur.close()

    await update.message.reply_text(
        f"✅ Ramalan {mention} {status_text}"
    )


async def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT,
            handle_message
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
