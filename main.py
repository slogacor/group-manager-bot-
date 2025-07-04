from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"
GROUP_ID = -1002883903673  # ganti dengan ID grup kamu

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # cek apakah ada argumen user_id atau username di command /unban
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

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("unban", unban))

    print("Bot aktif...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
