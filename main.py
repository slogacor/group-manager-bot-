from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
import json
from datetime import datetime, timezone, timedelta

BOT_TOKEN = "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"
GROUP_ID = -1002883903673  # Ganti dengan ID grup kamu
OWNER_ID = 1305881282  # Ganti dengan user_id kamu sendiri

invited_data_file = "invited_users.json"

def load_data():
    try:
        with open(invited_data_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(invited_data_file, "w") as f:
        json.dump(data, f, indent=2)

async def kick_user(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    now = datetime.now(timezone.utc)
    to_delete = []

    for user_id_str, user_data in data.items():
        join_time = datetime.fromisoformat(user_data["join_time"])
        if now - join_time > timedelta(hours=24):
            user_id = int(user_id_str)
            try:
                await context.bot.ban_chat_member(GROUP_ID, user_id)
                await context.bot.unban_chat_member(GROUP_ID, user_id)
                print(f"[INFO] User {user_id} di-kick setelah 24 jam.")
                to_delete.append(user_id_str)
            except Exception as e:
                print(f"[ERROR] Gagal kick user {user_id}: {e}")

    if to_delete:
        for uid in to_delete:
            del data[uid]
        save_data(data)

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    for member in update.message.new_chat_members:
        invited_by = update.message.from_user
        if invited_by.id == OWNER_ID:
            user_data = {
                "user_id": member.id,
                "username": member.username,
                "first_name": member.first_name,
                "join_time": datetime.now(timezone.utc).isoformat()
            }
            data[str(member.id)] = user_data
            save_data(data)
            await update.message.reply_text(
                f"✅ @{member.username or member.first_name} telah ditambahkan ke data undangan."
            )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot siap. Aku akan mencatat anggota yang kamu undang dan kick otomatis setelah 24 jam."
    )

async def cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("📭 Belum ada data undangan.")
        return
    text = json.dumps(data, indent=2)
    await update.message.reply_text(f"<pre>{text}</pre>", parse_mode="HTML")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cek", cek))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))

    # Pastikan job queue tidak None sebelum pakai run_repeating
    if app.job_queue is None:
        raise RuntimeError("JobQueue tidak tersedia, pastikan python-telegram-bot diinstall dengan [job-queue]")

    app.job_queue.run_repeating(kick_user, interval=3600, first=10)

    print("🤖 Bot aktif...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()
    asyncio.run(main())
