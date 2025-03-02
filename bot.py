import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    await update.message.reply_text("Привет! Я ваш бот. 🚀")

def main():
    # Создаем приложение и передаем токен
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start))
    
    # Запускаем бота
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
