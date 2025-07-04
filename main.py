import asyncio
from datetime import datetime
from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ChatMemberHandler
)

# 🧠 Menyimpan waktu join user sementara (RAM)
user_join_times = {}

# 🔹 Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Saya adalah bot pengelola grup. 👋")

# 🔹 Ketika member join ke grup
async def handle_member_update(update: ChatMemberUpdated, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member
    if member.new_chat_member.status == "member":
        user_id = member.from_user.id
        chat_id = update.chat.id
        join_time = datetime.utcnow()
        user_join_times[(chat_id, user_id)] = join_time
        await context.bot.send_message(chat_id, f"👤 {member.from_user.full_name} telah bergabung. Akan dikick dalam 24 jam.")
        asyncio.create_task(schedule_kick(context, chat_id, user_id, join_time))

# 🔹 Fungsi kick setelah 24 jam
async def schedule_kick(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, join_time: datetime):
    await asyncio.sleep(24 * 60 * 60)  # 24 jam
    now = datetime.utcnow()
    if user_join_times.get((chat_id, user_id)) == join_time:
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.unban_chat_member(chat_id, user_id)  # Supaya bisa join lagi nanti
            await context.bot.send_message(chat_id, f"👢 User {user_id} telah dikick setelah 24 jam.")
            del user_join_times[(chat_id, user_id)]
        except Exception as e:
            print(f"❌ Gagal kick {user_id}: {e}")

# 🔹 Fungsi utama
async def main():
    # Ganti dengan token bot kamu
    TOKEN = "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatMemberHandler(handle_member_update, ChatMemberHandler.CHAT_MEMBER))

    print("🤖 Bot Group Manager aktif!")
    await app.run_polling()

# 🔹 Jalankan dengan asyncio (tanpa konflik loop)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "event loop is closed" in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main())
