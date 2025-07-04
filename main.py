import os
import json
import asyncio
from datetime import datetime, timezone
from telegram import Update, ChatMemberUpdated
from telegram.ext import ApplicationBuilder, CommandHandler, ChatMemberHandler, ContextTypes

JSON_FILE = "joined_members.json"

def load_data():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_data(data):
    with open(JSON_FILE, "w") as f:
        json.dump(data, f)

user_join_times = load_data()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Halo! Bot Group Manager aktif.")

async def handle_member_update(update: ChatMemberUpdated, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member
    if member.new_chat_member.status == "member":
        chat_id = str(update.chat.id)
        user_id = str(member.from_user.id)
        join_time = datetime.now(timezone.utc).isoformat()

        if chat_id not in user_join_times:
            user_join_times[chat_id] = {}
        user_join_times[chat_id][user_id] = join_time
        save_data(user_join_times)

        await context.bot.send_message(chat_id=chat_id,
            text=f"Selamat datang {member.from_user.full_name}! Kamu akan dikick dalam 24 jam.")

        context.application.create_task(schedule_kick(context, chat_id, user_id, join_time))

async def schedule_kick(context, chat_id, user_id, join_time_str):
    await asyncio.sleep(24 * 60 * 60)  # ganti 60 detik untuk testing
    now = datetime.now(timezone.utc)
    join_time = datetime.fromisoformat(join_time_str)

    if user_join_times.get(chat_id, {}).get(user_id) == join_time_str:
        try:
            await context.bot.ban_chat_member(chat_id, int(user_id))
            await context.bot.unban_chat_member(chat_id, int(user_id))
            await context.bot.send_message(chat_id, f"👢 {user_id} telah dikick setelah 24 jam.")
        except Exception as e:
            print(f"Gagal kick {user_id}: {e}")
        finally:
            user_join_times[chat_id].pop(user_id, None)
            if not user_join_times[chat_id]:
                user_join_times.pop(chat_id)
            save_data(user_join_times)

async def recheck_pending_kicks(application):
    now = datetime.now(timezone.utc)
    for chat_id, users in list(user_join_times.items()):
        for user_id, join_time_str in list(users.items()):
            join_time = datetime.fromisoformat(join_time_str)
            elapsed = (now - join_time).total_seconds()
            remaining = (24 * 60 * 60) - elapsed
            if remaining <= 0:
                await schedule_kick(application.bot, chat_id, user_id, join_time_str)
            else:
                application.create_task(schedule_kick(application.bot, chat_id, user_id, join_time_str))

async def main():
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        raise RuntimeError("Environment variable TOKEN belum diset!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatMemberHandler(handle_member_update, ChatMemberHandler.CHAT_MEMBER))

    # Mulai aplikasi, tapi jangan pakai app.run_polling() langsung
    await app.start()
    print("🤖 Bot Group Manager aktif!")

    # Jalankan recheck_pending_kicks setelah app start
    await recheck_pending_kicks(app)

    # Mulai polling (block sampai bot berhenti)
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        print(f"Runtime error: {e}")
