import asyncio
from datetime import datetime, timedelta
import json
from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ChatMemberHandler,
    ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"
MEMBER_FILE = "joined_members.json"

def save_member(user_id, chat_id):
    try:
        with open(MEMBER_FILE, "r") as f:
            data = json.load(f)
    except:
        data = []

    expire = (datetime.now() + timedelta(hours=24)).isoformat()
    data.append({"user_id": user_id, "chat_id": chat_id, "expire": expire})

    with open(MEMBER_FILE, "w") as f:
        json.dump(data, f)

async def kick_old_members(app):
    try:
        with open(MEMBER_FILE, "r") as f:
            data = json.load(f)
    except:
        return

    now = datetime.now()
    new_data = []
    for member in data:
        expire_time = datetime.fromisoformat(member["expire"])
        if now >= expire_time:
            try:
                await app.bot.ban_chat_member(member["chat_id"], member["user_id"])
                await app.bot.unban_chat_member(member["chat_id"], member["user_id"])
            except Exception as e:
                print(f"Gagal kick {member['user_id']}: {e}")
        else:
            new_data.append(member)

    with open(MEMBER_FILE, "w") as f:
        json.dump(new_data, f)

async def member_update(update: ChatMemberUpdated, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_member.new_chat_member.status == "member":
        user = update.chat_member.from_user
        chat = update.chat_member.chat
        save_member(user.id, chat.id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Bot ini akan otomatis mengeluarkan member setelah 24 jam. ⏰")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(kick_old_members(app)), 'interval', minutes=1)
    scheduler.start()

    app.add_handler(ChatMemberHandler(member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("start", start))

    print("🤖 Bot Group Manager aktif!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
