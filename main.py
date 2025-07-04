from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ChatMemberHandler,
)
from datetime import datetime
import asyncio
import json
import os

JSON_FILE = "joined_members.json"

def load_data():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r") as f:
                data = json.load(f)
                return {
                    tuple(map(int, k.split("_"))): datetime.fromisoformat(v)
                    for k, v in data.items()
                }
        except Exception as e:
            print(f"Error load JSON: {e}")
            return {}
    return {}

def save_data(data):
    try:
        serializable_data = {f"{k[0]}_{k[1]}": v.isoformat() for k, v in data.items()}
        with open(JSON_FILE, "w") as f:
            json.dump(serializable_data, f)
        print(f"Saved data to {JSON_FILE}, entries: {len(data)}")
    except Exception as e:
        print(f"Error saving JSON: {e}")

user_join_times = load_data()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Halo! Bot Group Manager aktif.")

async def cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_join_times:
        await update.message.reply_text("Data JSON masih kosong.")
        return
    pesan = "Data anggota yang join:\n"
    for (chat_id, user_id), join_time in user_join_times.items():
        pesan += f"ChatID {chat_id}, UserID {user_id}: {join_time.isoformat()}\n"
    await update.message.reply_text(pesan)

async def handle_member_update(update: ChatMemberUpdated, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member
    if member.new_chat_member.status == "member":
        chat_id = update.chat.id
        user_id = member.from_user.id
        join_time = datetime.utcnow()
        user_join_times[(chat_id, user_id)] = join_time
        save_data(user_join_times)
        print(f"User {user_id} joined chat {chat_id} at {join_time.isoformat()}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Selamat datang {member.from_user.full_name}! Kamu akan dikick dalam 24 jam."
        )
        asyncio.create_task(schedule_kick(context, chat_id, user_id, join_time))

async def schedule_kick(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, join_time: datetime):
    await asyncio.sleep(24 * 60 * 60)  # 24 jam, bisa diganti 60 detik utk testing
    if user_join_times.get((chat_id, user_id)) == join_time:
        try:
            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            if chat_member.status == "member":
                await context.bot.ban_chat_member(chat_id, user_id)
                await context.bot.unban_chat_member(chat_id, user_id)
                await context.bot.send_message(chat_id, f"👢 {user_id} telah dikick setelah 24 jam.")
                print(f"Kicked user {user_id} from chat {chat_id}")
        except Exception as e:
            print(f"Gagal kick {user_id}: {e}")
        finally:
            user_join_times.pop((chat_id, user_id), None)
            save_data(user_join_times)

if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN") or "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cek", cek))
    app.add_handler(ChatMemberHandler(handle_member_update, ChatMemberHandler.CHAT_MEMBER))

    print("🤖 Bot Group Manager aktif!")
    app.run_polling()
