from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, CallbackQueryHandler, filters
)
from datetime import datetime, timedelta, UTC
import asyncio
import json
import os

JSON_FILE = "verified_users.json"
PENDING = {}

# Load verified users dari file
def load_verified():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

# Save verified users ke file
def save_verified(data):
    with open(JSON_FILE, "w") as f:
        json.dump(data, f)

verified_users = load_verified()

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot verifikasi aktif!")

# Command /cek untuk melihat user yang sudah verifikasi
async def cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not verified_users:
        await update.message.reply_text("📭 Belum ada user yang verifikasi.")
        return

    pesan = "📋 List user yang sudah verifikasi:\n"
    for key, time_str in verified_users.items():
        chat_id, user_id = key.split("_")
        pesan += f"- Chat: {chat_id}, User: {user_id}, waktu: {time_str}\n"

    await update.message.reply_text(pesan)

# Handle user baru join (lebih akurat daripada ChatMemberHandler)
async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    for user in update.message.new_chat_members:
        user_id = user.id
        full_name = user.full_name

        # Tombol verifikasi
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Verifikasi", callback_data=f"verify_{chat_id}_{user_id}")]
        ])

        msg = await update.message.reply_text(
            f"Halo {full_name}, silakan klik tombol verifikasi di bawah ini dalam waktu 2 menit.",
            reply_markup=keyboard
        )

        PENDING[(chat_id, user_id)] = {
            "time": datetime.now(UTC),
            "message_id": msg.message_id
        }

        asyncio.create_task(schedule_verification_kick(context, chat_id, user_id))

# Handle klik tombol verifikasi
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("verify_"):
        return

    _, chat_id_str, user_id_str = query.data.split("_")
    chat_id = int(chat_id_str)
    user_id = int(user_id_str)

    if update.effective_user.id != user_id:
        await query.edit_message_text("⚠️ Hanya pengguna yang diminta yang bisa verifikasi.")
        return

    verified_users[f"{chat_id}_{user_id}"] = datetime.now(UTC).isoformat()
    save_verified(verified_users)
    PENDING.pop((chat_id, user_id), None)

    await query.edit_message_text("✅ Kamu berhasil diverifikasi. Selamat bergabung!")

# Jadwal kick jika tidak verifikasi dalam 2 menit
async def schedule_verification_kick(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    await asyncio.sleep(2 * 60)  # 2 menit

    if (chat_id, user_id) in PENDING:
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.unban_chat_member(chat_id, user_id)
            await context.bot.send_message(
                chat_id,
                f"👢 <a href='tg://user?id={user_id}'>User</a> dikick karena tidak verifikasi.",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Gagal kick user: {e}")
        finally:
            PENDING.pop((chat_id, user_id), None)

# Jalankan bot
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN") or "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cek", cek))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot verifikasi aktif!")
    app.run_polling()
