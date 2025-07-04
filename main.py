from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from datetime import datetime, timedelta
import asyncio, os, json

TOKEN = os.getenv("BOT_TOKEN") or "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"
JSON_FILE = "verifikasi_data.json"

# ======== JSON LOAD / SAVE ==========
def load_data():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=2)

user_data = load_data()

# ========= VERIFIKASI ===============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot verifikasi aktif!")

async def handle_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    key = f"{chat_id}_{user_id}"

    # Sudah diverifikasi
    if key in user_data and user_data[key]["verified"]:
        return

    # Tambahkan ke data
    if key not in user_data:
        user_data[key] = {
            "join_time": datetime.utcnow().isoformat(),
            "verified": False
        }
        save_data(user_data)

        # Kirim tombol verifikasi
        button = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("✅ Verifikasi Sekarang", callback_data=f"verif_{chat_id}_{user_id}")
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"👋 Selamat datang {user.full_name}!\nTekan tombol di bawah ini untuk verifikasi dalam 5 menit.",
            reply_markup=button
        )
        asyncio.create_task(kick_if_not_verified(context, chat_id, user_id))

# ========= VERIFIKASI BUTTON ===========
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("verif_"):
        return

    _, chat_id, user_id = data.split("_")
    key = f"{chat_id}_{user_id}"

    if key in user_data and not user_data[key]["verified"]:
        user_data[key]["verified"] = True
        save_data(user_data)
        await query.edit_message_text("✅ Verifikasi berhasil! Selamat bergabung.")
    else:
        await query.edit_message_text("⚠️ Verifikasi gagal atau sudah dilakukan.")

# ========= KICK LOGIC ===========
async def kick_if_not_verified(context, chat_id, user_id):
    await asyncio.sleep(300)  # 5 menit
    key = f"{chat_id}_{user_id}"
    if key in user_data and not user_data[key]["verified"]:
        try:
            await context.bot.ban_chat_member(chat_id, int(user_id))
            await context.bot.unban_chat_member(chat_id, int(user_id))
            await context.bot.send_message(chat_id, f"👢 <a href='tg://user?id={user_id}'>User</a> dikeluarkan karena tidak verifikasi.", parse_mode="HTML")
        except Exception as e:
            print(f"Gagal kick: {e}")
        finally:
            user_data.pop(key, None)
            save_data(user_data)

# ========= CEK DATA ===========
async def cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_data:
        await update.message.reply_text("📂 Data kosong.")
        return

    msg = "📊 Data verifikasi:\n"
    for k, v in user_data.items():
        chat_id, user_id = k.split("_")
        status = "✅" if v["verified"] else "❌"
        msg += f"UserID {user_id} ({chat_id}): {status}\n"
    await update.message.reply_text(msg[:4000])

# ========= SETUP ===========
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cek", cek))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_message))
    app.add_handler(CallbackQueryHandler(handle_button))

    print("🤖 Bot verifikasi aktif!")
    app.run_polling()
