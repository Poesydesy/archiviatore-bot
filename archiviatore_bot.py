import time
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.background import BackgroundScheduler

# Inserisci qui il tuo token Telegram
import os
TOKEN = os.getenv("TOKEN")

# ID del topic dove archiviare i messaggi
ARCHIVE_TOPIC_ID = 123456  # ← Sostituisci con l’ID del tuo topic "Archivio"

# Dizionario per tenere traccia dei messaggi da archiviare
messages_to_archive = {}

# Gestione dei messaggi ricevuti
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.reply_to_message:
        if update.message.text.lower() == "archivia subito":
            try:
                await context.bot.copy_message(
                    chat_id=update.message.chat_id,
                    from_chat_id=update.message.chat_id,
                    message_id=update.message.reply_to_message.message_id,
                    message_thread_id=ARCHIVE_TOPIC_ID
                )
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.reply_to_message.message_id
                )
                await update.message.delete()
                print(f"✅ Archiviazione immediata completata: {update.message.reply_to_message.message_id}")
            except Exception as e:
                print(f"⚠️ Errore durante archiviazione immediata: {e}")
        else:
            msg_id = update.message.reply_to_message.message_id
            messages_to_archive[msg_id] = {
                "chat_id": update.message.chat_id,
                "message_id": msg_id,
                "timestamp": time.time()
            }
            await update.message.delete()
            print(f"🕒 Messaggio programmato per archiviazione: {msg_id}")

# Controllo ogni 10 secondi
async def archive_checker(context: ContextTypes.DEFAULT_TYPE):
    now = time.time()
    bot = context.bot
    for msg_id in list(messages_to_archive):
        data = messages_to_archive[msg_id]
        if now - data['timestamp'] >= 60:
            try:
                await bot.copy_message(
                    chat_id=data['chat_id'],
                    from_chat_id=data['chat_id'],
                    message_id=data['message_id'],
                    message_thread_id=ARCHIVE_TOPIC_ID
                )
                print(f"✅ Messaggio copiato dopo 1 minuto: {msg_id}")
                try:
                    await bot.delete_message(
                        chat_id=data['chat_id'],
                        message_id=data['message_id']
                    )
                    print(f"✅ Messaggio originale cancellato dopo 1 minuto: {msg_id}")
                except Exception as e:
                    print(f"⚠️ Messaggio troppo vecchio, non cancellabile: {msg_id}")
                    await bot.send_message(
                        chat_id=data['chat_id'],
                        text="⚠️ Il messaggio non è stato cancellato perché ha più di 48 ore.",
                        message_thread_id=ARCHIVE_TOPIC_ID
                    )
                del messages_to_archive[msg_id]
            except Exception as e:
                print(f"⚠️ Errore durante archiviazione ritardata: {e}")
                del messages_to_archive[msg_id]

# Avvio bot compatibile con Render
import asyncio

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_message))

    await app.initialize()
    app.job_queue.run_repeating(archive_checker, interval=10)
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

asyncio.run(main())
