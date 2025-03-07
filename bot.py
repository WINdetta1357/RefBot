import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка токена из переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Определение функции для создания клавиатуры
def build_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [("Меньше 14", "age_less_14"), ("С 14 по 18", "age_14_18"), ("Больше 18", "age_more_18")]
    ]
    await update.message.reply_text(
        "👋 Привет! Пожалуйста, выберите вашу возрастную категорию:",
        reply_markup=build_keyboard(keyboard)
    )

# Обработчик нажатия кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "age_less_14":
        await query.edit_message_text(text="Вы выбрали категорию: Меньше 14")
    elif data == "age_14_18":
        await query.edit_message_text(text="Вы выбрали категорию: С 14 по 18")
    elif data == "age_more_18":
        await query.edit_message_text(text="Вы выбрали категорию: Больше 18")

# Основная функция
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    
    application.run_polling()

if __name__ == "__main__":
    main()
