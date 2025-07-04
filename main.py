from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters
)
import json
from datetime import datetime

BOT_TOKEN = "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"
GROUP_ID = -1002883903673  # Ganti dengan ID grup kamu
OWNER_ID = 1305881282  # Ganti dengan user_id kamu sendiri

invited_data_file = "invited_users.json"

# Load existing invited users data
def load_data():
    try:
        with open(invited_data_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save data
def save_data(data):
    with open(invited_data_file, "w") as f:
        json.dump(data, f, indent=2)

# Deteksi anggota baru
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    for member in update.message.new_chat_members:
        invited_by = update.message.from_user

        if invited_by.id == OWNER_ID:
            user_data = {
                "user_id": member.id,
                "username": member.username,
                "first_name": member.first_name,
                "join_time": datetime.utcnow().isoformat()
            }
            data[str(member.id)] = user_data
            save_data(data)

            await update.message.reply_text(
                f"✅ @{member.username or member.first_name} telah ditambahkan ke data undangan."
            )

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot siap. Aku akan mencatat anggota yang kamu undang.")

# /cek command
async def cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("📭 Belum ada data undangan.")
        return
    text = json.dumps(data, indent=2)
    await update.message.reply_text(f"<pre>{text}</pre>", parse_mode="HTML")

# Start Bot
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cek", cek))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))

    print("🤖 Bot aktif...")
    await app.run_polling()

# Run Async
if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()

    asyncio.run(main())

