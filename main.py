import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Fungsi handler /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Saya bot pengelola grup. Siap membantu!")

async def main():
    # Ganti dengan token bot kamu
    TOKEN = "8196752676:AAENfAaWctBNS6hcNNS-bdRwbz4_ntOHbFs"

    app = Application.builder().token(TOKEN).build()

    # Tambahkan handler
    app.add_handler(CommandHandler("start", start))

    print("🤖 Bot Group Manager aktif!")

    # Langsung jalankan polling
    await app.run_polling()

if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except RuntimeError as e:
        # Jika loop sudah berjalan, jalankan langsung tanpa run()
        if "event loop is already running" in str(e):
            import nest_asyncio
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
