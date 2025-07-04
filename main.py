import os
import asyncio
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ChatMemberHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = os.getenv("TOKEN")
member_join_times = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Saya bot pengelola grup. Saya akan menghapus member setelah 24 jam.")

async def handle_member_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = update.chat_member
    user = chat_member.new_chat_member.user

    if chat_member.old_chat_member.status == "left" and chat_member.new_chat_member.status == "member":
        member_id = user.id
        join_time = datetime.now()
        member_join_times[member_id] = {
            "chat_id": chat_member.chat.id,
            "join_time": join_time,
        }
        print(f"✅ {user.full_name} join jam {join_time}")

async def kick_old_members(app):
    now = datetime.now()
    to_kick = []

    for user_id, data in list(member_join_times.items()):
        if now - data["join_time"] > timedelta(hours=24):
            to_kick.append((user_id, data["chat_id"]))

    for user_id, chat_id in to_kick:
        try:
            await app.bot.ban_chat_member(chat_id, user_id)
            await app.bot.unban_chat_member(chat_id, user_id)
            print(f"👢 Kick user {user_id} dari chat {chat_id}")
            del member_join_times[user_id]
        except Exception as e:
            print(f"❌ Gagal kick {user_id}: {e}")

async def run_bot():
    print("🤖 Bot Group Manager aktif!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatMemberHandler(handle_member_join, ChatMemberHandler.CHAT_MEMBER))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(kick_old_members(app)), "interval", minutes=1)
    scheduler.start()

    await app.run_polling()  # ✅ ini yang benar

# 👇 Jalankan langsung
if __name__ == "__main__":
    asyncio.run(run_bot())
