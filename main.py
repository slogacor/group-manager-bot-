# Tambahkan di bagian import
from telegram import Update, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ChatMemberHandler, CallbackQueryHandler
)
from datetime import datetime, timedelta, UTC
import asyncio
import json
import os

JSON_FILE = "verified_users.json"
PENDING = {}

def load_verified():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_verified(data):
    with open(JSON_FILE, "w") as f:
        json.dump(data, f)

verified_users = load_verified()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot verifikasi aktif!")

# Saat anggota join
async def handle_member(update: ChatMemberUpdated, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member
    if member.new_chat_member.status == "member":
        chat_id = update.chat.id
        user_id = member.from_user.id
        full_name = member.from_user.full_name

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Verifikasi", callback_data=f"verify_{chat_id}_{user_id}")]
        ])

        msg = await context.bot.send_message(
            chat_id,
            text=f"Halo {full_name}, klik tombol verifikasi di bawah ini dalam 2 menit.",
            reply_markup=keyboard
        )

        PENDING[(chat_id, user_id)] = {
            "time": datetime.now(UTC),
            "message_id": msg.message_id
        }

        asyncio.create_task(schedule_verification_kick(context, chat_id, user_id, 2 * 60))  # 2 menit

# Saat user klik tombol
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

    await query.edit_message_text("✅ Kamu berhasil diverifikasi. Tapi kamu akan dikick 10 menit lagi.")

    # Jadwalkan kick 10 menit setelah verifikasi
    asyncio.create_task(schedule_verification_kick(context, chat_id, user_id, 10 * 60))  # 10 menit

# Fungsi untuk jadwal kick
async def schedule_verification_kick(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, delay: int):
    await asyncio.sleep(delay)

    try:
        await context.bot.ban_chat_member(chat_id, user_id)
        await context.bot.unban_chat_member(chat_id, user_id)
        await context.bot.send_message(
            chat_id,
            f"👢 <a href='tg://user?id={user_id}'>User</a> telah dikick setelah {delay // 60} menit.",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Gagal kick user {user_id}: {e}")
    finally:
        PENDING.pop((chat_id, user_id), None)
        verified_users.pop(f"{chat_id}_{user_id}", None)
        save_verified(verified_users)

# /cek command
async def cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not verified_users:
        await update.message.reply_text("📭 Belum ada user yang verifikasi.")
        return

    pesan = "📋 List user yang sudah verifikasi:\n"
    for key, time_str in verified_users.items():
        chat_id, user_id = key.split("_")
        pesan += f"- Chat: {chat_id}, User: {user_id}, waktu: {time_str}\n"

    await update.message.reply_text(pesan)

# Main
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cek", cek))
    app.add_handler(ChatMemberHandler(handle_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot verifikasi aktif!")
    app.run_polling()
