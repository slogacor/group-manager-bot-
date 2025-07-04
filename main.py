from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ChatMemberHandler,
)
from datetime import datetime
import asyncio

# Simpan waktu join
user_join_times = {}

# Perintah /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Halo! Bot Group Manager aktif.")

# Saat anggota baru join
async def handle_member_update(update: ChatMemberUpdated, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member
    if member.new_chat_member.status == "member":
        chat_id = update.chat.id
        user_id = member.from_user.id
        join_time = datetime.utcnow()
        user_join_times[(chat_id, user_id)] = join_time

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Selamat datang {member.from_user.full_name}! Kamu akan dikick dalam 24 jam."
        )

        # Jadwalkan kick
        asyncio.create_task(schedule_kick(context, chat_id, user_id, join_time))

# Fungsi kick setelah 24 jam
async def schedule_kick(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, join_time: datetime):
    await asyncio.sleep(24 * 60 * 60)  # Bisa diganti 60 untuk testing
    now = datetime.utcnow()

    if user_join_times.get((chat_id, user_id)) == join_time:
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.unban_chat_member(chat_id, user_id)
            await context.bot.send_message(chat_id, f"👢 {user_id} telah dikick setelah 24 jam.")
        except Exception as e:
            print(f"Gagal kick {user_id}: {e}")
        finally:
            user_join_times.pop((chat_id, user_id), None)

# Main entry
if __name__ == "__main__":
    import os

    TOKEN = os.getenv("BOT_TOKEN") or "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatMemberHandler(handle_member_update, ChatMemberHandler.CHAT_MEMBER))

    print("🤖 Bot Group Manager aktif!")
    app.run_polling()
