import time
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

# 🔐 Token del tuo bot
TOKEN = '8378141191:AAHVrZZfLD2MDuD5vTjJiU_mRC6IBbo96cA'

# 🧵 ID del topic "Archivio"
ARCHIVE_TOPIC_ID = 111

# Dizionario per archiviazione ritardata
messages_to_archive = {}

# 🔁 Gestione dei comandi
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        print("❌ Nessun messaggio ricevuto")
        return

    if not message.reply_to_message:
        print("⚠️ Il comando non è una risposta")
        return

    command = message.text.strip().lower()
    print(f"📥 Comando ricevuto: {command}")

    if command not in ['archivia', 'archivia subito']:
        print("⛔ Comando non riconosciuto")
        return

    original = message.reply_to_message
    msg_id = original.message_id
    chat_id = original.chat.id

    # Cancella il comando
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        print(f"🧹 Comando cancellato: {command}")
    except Exception as e:
        print(f"❌ Errore cancellando il comando: {e}")

    if command == 'archivia subito':
        try:
            await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=chat_id,
                message_id=msg_id,
                message_thread_id=ARCHIVE_TOPIC_ID
            )
            print(f"✅ Messaggio copiato subito: {msg_id}")
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                print(f"🗑️ Messaggio originale cancellato subito: {msg_id}")
            except Exception as e:
                print(f"⚠️ Messaggio troppo vecchio, non cancellabile: {msg_id}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Il messaggio non è stato cancellato perché ha più di 48 ore.",
                    message_thread_id=ARCHIVE_TOPIC_ID
                )
        except Exception as e:
            print(f"❌ Errore archivia subito: {e}")
    else:
        messages_to_archive[msg_id] = {
            'chat_id': chat_id,
            'message_id': msg_id,
            'timestamp': time.time()
        }
        print(f"⏳ Messaggio registrato per archiviazione ritardata: {msg_id}")

# ⏱️ Controllo ogni 10 secondi
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
                    print(f"🗑️ Messaggio originale cancellato dopo 1 minuto: {msg_id}")
                except Exception as e:
                    print(f"⚠️ Messaggio troppo vecchio, non cancellabile: {msg_id}")
                    await bot.send_message(
                        chat_id=data['chat_id'],
                        text="⚠️ Il messaggio non è stato cancellato perché ha più di 48 ore.",
                        message_thread_id=ARCHIVE_TOPIC_ID
                    )
            except Exception as e:
                print(f"❌ Errore durante archiviazione ritardata: {e}")
            del messages_to_archive[msg_id]

# 🚀 Avvio bot
app = Application.builder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_message))
app.job_queue.run_repeating(archive_checker, interval=10)
app.run_polling()
