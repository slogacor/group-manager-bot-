from telegram import Update, ChatInviteLink, User
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from datetime import datetime, timedelta
import json, os

# === Konfigurasi ===
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"
GROUP_ID = int(os.getenv("GROUP_ID") or "-1002883903673")

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

# === Fungsi mengundang user
async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Format: /invite username")
        return

    username = context.args[0].lstrip("@")

    try:
        link: ChatInviteLink = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            member_limit=1,
            creates_join_request=False
        )

        user: User = await context.bot.get_chat(f"@{username}")
        user_id = user.id if user else None

        joined_users[username.lower()] = {
            "username": username,
            "user_id": user_id,
            "join_time": datetime.utcnow().isoformat()
        }
        save_joined_users()

        # Coba kirim DM ke user (jika mereka sudah /start bot)
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=(
                    f"👋 Halo @{username}!\n\n"
                    f"Admin telah mengundangmu ke grup.\n"
                    f"🔗 Klik link berikut untuk join:\n{link.invite_link}\n\n"
                    f"⚠️ Link berlaku 1x dan kamu akan dikeluarkan otomatis setelah 24 jam."
                )
            )
        except Exception as dm_error:
            await update.message.reply_text(
                f"⚠️ Tidak bisa mengirim DM ke @{username}. "
                f"Pastikan mereka sudah memulai chat dengan bot (/start).\n\n"
                f"📎 Link undangan: {link.invite_link}"
            )

        # Jadwalkan untuk kick setelah 24 jam
        context.job_queue.run_once(
            kick_user,
            when=timedelta(hours=24),
            data={"username": username.lower()},
            name=username.lower()
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Gagal mengundang @{username}: {e}")

# === Fungsi Kick
async def kick_user(context: ContextTypes.DEFAULT_TYPE):
    username = context.job.data["username"]
    data = joined_users.get(username)

    if not data:
        return

    user_id = data.get("user_id")

    if not user_id:
        try:
            # Coba ambil dari daftar admin (opsional backup)
            chat_members = await context.bot.get_chat_administrators(GROUP_ID)
            for member in chat_members:
                if member.user.username and member.user.username.lower() == username:
                    user_id = member.user.id
                    joined_users[username]["user_id"] = user_id
                    save_joined_users()
                    break
        except Exception as e:
            print(f"[WARN] Tidak bisa ambil ID @{username}: {e}")
            return

    if user_id:
        try:
            await context.bot.ban_chat_member(GROUP_ID, user_id, until_date=int(datetime.utcnow().timestamp()) + 60)
            await context.bot.unban_chat_member(GROUP_ID, user_id)
            print(f"[INFO] @{username} berhasil dikeluarkan.")

            # Hapus dari data
            del joined_users[username]
            save_joined_users()

        except Exception as e:
            print(f"[ERROR] Gagal kick @{username}: {e}")
    else:
        print(f"[SKIP] Tidak menemukan user_id untuk @{username}")

# === /cek untuk lihat JSON
async def cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not joined_users:
        await update.message.reply_text("📭 Tidak ada data member.")
        return

    json_str = json.dumps(joined_users, indent=2)
    await update.message.reply_text(f"<pre>{json_str}</pre>", parse_mode="HTML")

# === /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot siap. Gunakan /invite username")

# === Main
async def main():
    load_joined_users()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("invite", invite))
    app.add_handler(CommandHandler("cek", cek))

    print("🚀 Bot berjalan...")
    await app.run_polling()

# === Railway/Nest Asyncio Friendly
if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except RuntimeError:
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.get_event_loop().run_until_complete(main())
