import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, CallbackContext
from dotenv import load_dotenv

# --- Настройки логов ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- Загрузка переменных окружения ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Добавь в Railway после получения домена
PORT = int(os.getenv("PORT", 5000))  # Для вебхука

# --- Состояния ---
ASK_AGE = 1
user_age = {}

# --- Обработчик /start ---
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("14-17 лет", callback_data="age_14_17")],
        [InlineKeyboardButton("18+ лет", callback_data="age_18_plus")]
    ]
    await update.message.reply_text("👋 Привет! Выбери свой возраст:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ASK_AGE

async def handle_age(update: Update, context: CallbackContext):
    """Обработка возраста"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    user_age[chat_id] = 14 if query.data == "age_14_17" else 18

    keyboard = [
        [InlineKeyboardButton("🏦 Банковские карты", callback_data="category_banks")],
        [InlineKeyboardButton("🔍 Сравнить карты", callback_data="compare_cards")],
        [InlineKeyboardButton("🎁 Акции", callback_data="promo")]
    ]
    await query.edit_message_text("🎮 Выбери раздел:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def button_handler(update: Update, context: CallbackContext):
    """Обработка кнопок"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Ты нажал кнопку.")

def main():
    """Запуск бота"""
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={ASK_AGE: [CallbackQueryHandler(handle_age)]},
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))

    # --- Запуск бота ---
    if WEBHOOK_URL:
        logging.info("🚀 Запуск в режиме WEBHOOK")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
        )
    else:
        logging.info("🤖 Запуск в режиме POLLING")
        app.run_polling()

if __name__ == "__main__":
    main()
