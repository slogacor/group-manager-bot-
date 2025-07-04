from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ChatMemberHandler,
)
from datetime import datetime, timedelta
import asyncio
import json
import os

# File JSON
JSON_FILE = "joined_members.json"

# Load data dari JSON
def load_data():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            return json.load(f)
    return {}

# Simpan data ke JSON
def save_data(data):
    with open(JSON_FILE, "w") as f:
        json.dump(data, f)

# Ambil data awal
user_join_times = load_data()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Halo! Bot Group Manager aktif.")

# Saat member baru join
async def handle_member_update(update: ChatMemberUpdated, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member
    if member.new_chat_member.status == "member":
        chat_id = str(update.chat.id)
        user_id = str(member.from_user.id)
        join_time = datetime.utcnow().isoformat()

        if chat_id not in user_join_times:
            user_join_times[chat_id] = {}

        user_join_times[chat_id][user_id] = join_time
        save_data(user_join_times)

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Selamat datang {member.from_user.full_name}! Kamu akan dikick dalam 24 jam."
        )

        asyncio.create_task(schedule_kick(context, chat_id, user_id, join_time))

# Fungsi kick otomatis
async def schedule_kick(context, chat_id, user_id, join_time_str):
    await asyncio.sleep(24 * 60 * 60)  # 24 jam

    stored_time_str = user_join_times.get(chat_id, {}).get(user_id)
    if stored_time_str == join_time_str:
        try:
            await context.bot.ban_chat_member(int(chat_id), int(user_id))
            await context.bot.unban_chat_member(int(chat_id), int(user_id))
            await context.bot.send_message(int(chat_id), f"👢 <a href='tg://user?id={user_id}'>User</a> telah dikick setelah 24 jam.", parse_mode="HTML")
        except Exception as e:
            print(f"Gagal kick {user_id}: {e}")
        finally:
            user_join_times[chat_id].pop(user_id, None)
            if not user_join_times[chat_id]:
                user_join_times.pop(chat_id)
            save_data(user_join_times)

# Saat bot pertama dijalankan, jadwalkan ulang semua kick yang tertunda
async def recheck_pending_kicks(app):
    now = datetime.utcnow()
    for chat_id, users in user_join_times.items():
        for user_id, join_time_str in users.items():
            join_time = datetime.fromisoformat(join_time_str)
            remaining = (join_time + timedelta(hours=24)) - now
            if remaining.total_seconds() > 0:
                asyncio.create_task(schedule_kick(app.bot, chat_id, user_id, join_time_str))
            else:
                asyncio.create_task(schedule_kick(app.bot, chat_id, user_id, join_time_str))

# Main
async def main():
    TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatMemberHandler(handle_member_update, ChatMemberHandler.CHAT_MEMBER))

    print("🤖 Bot Group Manager aktif!")
    await recheck_pending_kicks(app)
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
