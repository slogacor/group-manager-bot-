from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime, timedelta
import json, os

# === Konfigurasi ===
BOT_TOKEN = "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"
GROUP_ID = -1002883903673  # ganti sesuai ID grup kamu

joined_users = {}

# === Simpan & Muat data user ke file JSON ===
def save_joined_users():
    with open("joined_users.json", "w") as f:
        json.dump(joined_users, f, indent=2)

def load_joined_users():
    global joined_users
    try:
        with open("joined_users.json", "r") as f:
            joined_users = json.load(f)
    except FileNotFoundError:
        joined_users = {}

# === Tangani saat user join
async def handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        join_time = datetime.utcnow().isoformat()
        joined_users[str(user.id)] = {
            "username": user.username or "-",
            "full_name": user.full_name,
            "join_time": join_time
        }
        save_joined_users()
        print(f"[JOIN] {user.full_name} ({user.id}) at {join_time}")

        # Jadwalkan auto-kick 24 jam dari sekarang
        context.job_queue.run_once(
            kick_user,
            when=timedelta(hours=24),
            data={"user_id": user.id},
            name=str(user.id)
        )

# === Kick user otomatis setelah 24 jam
async def kick_user(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.data["user_id"]
    try:
        await context.bot.ban_chat_member(GROUP_ID, user_id)
        await context.bot.unban_chat_member(GROUP_ID, user_id)
        print(f"[KICKED] {user_id} telah dikeluarkan setelah 24 jam.")
        joined_users.pop(str(user_id), None)
        save_joined_users()
    except Exception as e:
        print(f"[ERROR] Gagal mengeluarkan {user_id}: {e}")

# === Perintah /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot aktif. Member baru akan dikeluarkan otomatis setelah 24 jam.")

# === Perintah /cek
async def cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not joined_users:
        await update.message.reply_text("📭 Belum ada data user yang tercatat.")
        return

    pesan = "📋 Daftar user yang tercatat:\n"
    for user_id, info in joined_users.items():
        username = f"@{info['username']}" if info['username'] != "-" else info['full_name']
        waktu = info["join_time"]
        pesan += f"• {username} (ID: {user_id})\n  ⏰ {waktu}\n"

    await update.message.reply_text(pesan)

# === Program utama
async def main():
    load_joined_users()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cek", cek))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_join))

    print("🚀 Bot aktif dan siap mengeluarkan member setelah 24 jam...")
    await app.run_polling()

# === Jalankan
if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except RuntimeError as e:
        # Jika loop sudah berjalan (seperti di Railway), gunakan cara alternatif
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
