import time
import os
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")
ARCHIVE_TOPIC_ID = 111

messages_to_archive = {}

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

async def archive_checker(application: Application):
    while True:
        now = time.time()
        bot = application.bot
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
                        print(f"✅ Messaggio originale cancellato dopo 1 minuto
