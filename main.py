from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
import json
from datetime import datetime, timezone, timedelta

BOT_TOKEN = "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"
GROUP_ID = -1002883903673
OWNER_ID = 1305881282

invited_data_file = "invited_users.json"

def load_data():
    try:
        with open(invited_data_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(invited_data_file, "w") as f:
        json.dump(data, f, indent=2)

async def kick_user(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    now = datetime.now(timezone.utc)
    to_delete = []

    for user_id_str, user_data in data.items():
        join_time = datetime.fromisoformat(user_data["join_time"])
        if now - join_time > timedelta(hours=24):
            user_id = int(user_id_str)
            try:
                await context.bot.ban_chat_member(GROUP_ID, user_id)
                await context.bot.unban_chat_member(GROUP_ID, user_id)
                print(f"[INFO] User {user_id} di-kick setelah 24 jam.")
                to_delete.append(user_id_str)
            except Exception as e:
                print(f"[ERROR] Gagal kick user {user_id}: {e}")

    if to_delete:
        for uid in to_delete:
            del data[uid]
        save_data(data)

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    for member in update.message.new_chat_members:
        joined_by = update.message.from_user

        # Jika user join sendiri (via link atau publik)
        is_via_link = member.id == joined_by.id

        user_data = {
            "user_id": member.id,
            "username": member.username,
            "first_name": member.first_name,
            "join_time": datetime.now(timezone.utc).isoformat(),
            "invited_by": None if is_via_link else joined_by.id,
            "via_link": is_via_link
        }

        # Catat hanya jika dia join lewat link atau diundang owner
        if is_via_link or (joined_by and joined_by.id == OWNER_ID):
            data[str(member.id)] = user_data
            save_data(data)
            await update.message.reply_text(
                f"✅ @{member.username or member.first_name} telah dicatat. "
                + ("(via link)" if is_via_link else "(diundang oleh owner)")
            )



async def user_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    left_member = update.message.left_chat_member
    kicked_by = update.message.from_user

    if kicked_by and kicked_by.id == OWNER_ID:
        user_id = str(left_member.id)
        if user_id in data:
            del data[user_id]
            save_data(data)
            print(f"[INFO] Data user {user_id} dihapus karena dikick manual oleh owner.")
            await update.message.reply_text(f"🗑️ Data user {user_id} dihapus dari JSON karena kamu yang kick.")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Kirim perintah dengan user_id: /unban <user_id>")
        return

    user_id_str = context.args[0]
    try:
        user_id = int(user_id_str)
    except ValueError:
        await update.message.reply_text("User ID harus berupa angka.")
        return

    try:
        await context.bot.unban_chat_member(GROUP_ID, user_id)
        await update.message.reply_text(f"✅ Berhasil membuka blokir user {user_id}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal membuka blokir: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot siap. Aku akan mencatat anggota yang kamu undang dan kick otomatis setelah 24 jam."
    )

async def cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("📭 Belum ada data undangan.")
        return
    text = json.dumps(data, indent=2)
    await update.message.reply_text(f"<pre>{text}</pre>", parse_mode="HTML")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cek", cek))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, user_left))

    app.job_queue.run_repeating(kick_user, interval=3600, first=10)

    print("🤖 Bot aktif...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()
    asyncio.run(main())
