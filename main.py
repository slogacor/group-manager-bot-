from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)
import json
import requests
from datetime import datetime, timezone, timedelta

# --- Konstanta ---
BOT_TOKEN = "8196752676:AAH-EIup-MapoKDl5ayylgfqPk6EQeMti-c"
GROUP_ID = -1002883903673
OWNER_ID = 1305881282
invited_data_file = "invited_users.json"
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbxCwh7MjRs-i7cEWkVqYOpZprK7q3PjFX_p0MH5-FyVHXoqlvSJVPP7JiU4TmVzJXdnjA/exec"

HARDCODED_USERS = {
    "7216866087": {
        "username": "Onlyykiaa4",
        "first_name": "Only",
        "join_time": "2025-07-04T11:19:34.274170+00:00",
        "invited_by": "",
        "via_link": True,
        "out_time": ""
    },
    "6656314040": {
        "username": "Hainekenz",
        "first_name": "Hainekenz",
        "join_time": "2025-07-04T11:28:40.724792+00:00",
        "invited_by": 1305881282,
        "via_link": False,
        "out_time": ""
    },
    "8114552558": {
        "username": "OnePercentWeeklyBot",
        "first_name": "BTCUSDONEPERCENT_BOT",
        "join_time": "2025-07-04T11:45:11.294009+00:00",
        "invited_by": 1305881282,
        "via_link": False,
        "out_time": ""
    },
    "7678173969": {
        "username": "ONEPercentXauusDbot",
        "first_name": "XAUUSDONEPERCENT_BOT",
        "join_time": "2025-07-04T12:06:17.522355+00:00",
        "invited_by": 1305881282,
        "via_link": False,
        "out_time": ""
    }
}

def load_data():
    try:
        with open(invited_data_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(invited_data_file, "w") as f:
        json.dump(data, f, indent=2)

def inject_hardcoded_users():
    data = load_data()
    updated = False
    for uid, info in HARDCODED_USERS.items():
        if uid not in data:
            data[uid] = info
            updated = True
    if updated:
        save_data(data)
        print("[INIT] Hardcoded users ditambahkan ke database lokal.")

def send_to_google_sheet(user_data: dict):
    try:
        response = requests.post(GOOGLE_SHEET_URL, json=user_data)
        response.raise_for_status()
        print(f"[SHEET] Data dikirim: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Kirim ke Google Sheet gagal: {e}")

def delete_from_google_sheet(user_id):
    try:
        response = requests.post(GOOGLE_SHEET_URL, json={"action": "delete", "user_id": user_id})
        response.raise_for_status()
        print(f"[SHEET] Data user {user_id} dihapus.")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Gagal hapus dari Google Sheet: {e}")

def fetch_data_from_sheet():
    try:
        response = requests.get(GOOGLE_SHEET_URL)
        response.raise_for_status()
        data = response.json()
        filtered_data = {
            uid: info for uid, info in data.items() if info.get("join_time")
        }
        save_data(filtered_data)
        print("[INFO] Data berhasil diambil dan difilter dari Google Sheet.")
    except Exception as e:
        print(f"[ERROR] Gagal ambil data dari Google Sheet: {e}")

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    for member in update.message.new_chat_members:
        joined_by = update.message.from_user
        is_via_link = member.id == joined_by.id

        user_data = {
            "user_id": member.id,
            "username": member.username,
            "first_name": member.first_name,
            "join_time": datetime.now(timezone.utc).isoformat(),
            "invited_by": None if is_via_link else joined_by.id,
            "via_link": is_via_link,
            "out_time": ""
        }

        if is_via_link or (joined_by and joined_by.id == OWNER_ID):
            data[str(member.id)] = user_data
            save_data(data)
            send_to_google_sheet(user_data)

            await update.message.reply_text(
                f"✅ @{member.username or member.first_name} tercatat. "
                + ("(via link)" if is_via_link else "(diundang oleh owner)")
            )

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("24 Jam", callback_data=f"kick:{member.id}:24"),
                    InlineKeyboardButton("7 Hari", callback_data=f"kick:{member.id}:168"),
                    InlineKeyboardButton("30 Hari", callback_data=f"kick:{member.id}:720"),
                ]
            ])
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"Pilih durasi kick untuk @{member.username or member.first_name}:",
                reply_markup=keyboard
            )

async def handle_kick_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()

    try:
        _, user_id, hours = query.data.split(":")
        user_id = str(user_id)
        hours = int(hours)

        if user_id in data:
            join_time = datetime.fromisoformat(data[user_id]["join_time"])
            kick_time = join_time + timedelta(hours=hours)
            data[user_id]["kick_at"] = kick_time.isoformat()
            save_data(data)
            await query.edit_message_text(f"✅ Kick user ID {user_id} dalam {hours} jam berhasil diset.")
        else:
            await query.edit_message_text("❌ User tidak ditemukan di database.")
    except Exception as e:
        await query.edit_message_text(f"❌ Terjadi kesalahan: {e}")

async def user_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    left_member = update.message.left_chat_member
    user_id = str(left_member.id)

    if user_id in data:
        data[user_id]["out_time"] = datetime.now(timezone.utc).isoformat()
        save_data(data)
        send_to_google_sheet(data[user_id])
        print(f"[INFO] User {user_id} keluar, out_time diupdate.")
        await update.message.reply_text(f"📤 User {user_id} keluar. out_time dicatat.")

async def kick_user(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    now = datetime.now(timezone.utc)
    to_delete = []

    try:
        admins = await context.bot.get_chat_administrators(GROUP_ID)
        admin_ids = {admin.user.id for admin in admins}
    except Exception as e:
        print(f"[ERROR] Gagal mengambil admin grup: {e}")
        admin_ids = set()

    for user_id_str, user_data in list(data.items()):
        kick_at_str = user_data.get("kick_at")
        if not kick_at_str:
            continue
        try:
            kick_at = datetime.fromisoformat(kick_at_str)
            if now >= kick_at:
                user_id = int(user_id_str)
                if user_id in admin_ids:
                    print(f"[SKIP] User {user_id} adalah admin, tidak di-kick.")
                    continue

                await context.bot.ban_chat_member(GROUP_ID, user_id)
                await context.bot.unban_chat_member(GROUP_ID, user_id)
                print(f"[AUTO-KICK] User {user_id} di-kick otomatis.")
                data[user_id_str]["out_time"] = now.isoformat()
                send_to_google_sheet(data[user_id_str])
                to_delete.append(user_id_str)
        except Exception as e:
            print(f"[ERROR] Gagal proses kick untuk {user_id_str}: {e}")

    for uid in to_delete:
        del data[uid]
    save_data(data)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot aktif. Anggota yang bergabung akan dicatat dan bisa diatur untuk di-kick otomatis setelah waktu tertentu."
    )

async def cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("📭 Tidak ada data.")
        return
    text = json.dumps(data, indent=2)
    await update.message.reply_text(f"<pre>{text}</pre>", parse_mode="HTML")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan perintah: /unban <user_id>")
        return
    try:
        user_id = int(context.args[0])
        await context.bot.unban_chat_member(GROUP_ID, user_id)
        await update.message.reply_text(f"✅ User {user_id} berhasil di-unban.")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal unban: {e}")

async def main():
    fetch_data_from_sheet()
    inject_hardcoded_users()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cek", cek))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, user_left))
    app.add_handler(CallbackQueryHandler(handle_kick_duration, pattern="^kick:"))

    app.job_queue.run_repeating(kick_user, interval=60, first=10)

    print("🤖 Bot Telegram aktif...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
