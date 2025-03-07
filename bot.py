import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook
from fastapi import FastAPI
import uvicorn

# Настройки
TOKEN = os.getenv("BOT_TOKEN")  # Токен бота из переменных окружения
WEBHOOK_HOST = "https://refbot-production-c08c.up.railway.app"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Настройки веб-сервера
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
app = FastAPI()

# Переменные
user_data = {}

# Главное меню
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("Выбрать возраст"))

# Функция создания кнопок с возрастом
def age_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("18", "21", "25", "30")
    return keyboard

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет! Сколько тебе лет?", reply_markup=age_keyboard())

# Обработчик выбора возраста
@dp.message_handler(lambda message: message.text.isdigit())
async def age_selected(message: types.Message):
    age = int(message.text)
    user_data[message.from_user.id] = {"age": age}
    await message.answer(f"Тебе {age} лет. Выбери банк:", reply_markup=banks_keyboard())

# Функция клавиатуры банков
def banks_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Сбербанк", "Тинькофф", "Альфа-Банк")
    keyboard.add("Все карты")
    return keyboard

# Обработчик выбора банка
@dp.message_handler(lambda message: message.text in ["Сбербанк", "Тинькофф", "Альфа-Банк", "Все карты"])
async def bank_selected(message: types.Message):
    user_id = message.from_user.id
    bank = message.text
    user_data[user_id]["bank"] = bank
    await message.answer(f"Ты выбрал {bank}. Вот доступные карты:", reply_markup=cards_keyboard(bank))

# Функция клавиатуры карт
def cards_keyboard(bank):
    keyboard = InlineKeyboardMarkup()
    if bank == "Сбербанк":
        keyboard.add(InlineKeyboardButton("Карта 1", callback_data="sber_card_1"))
    elif bank == "Тинькофф":
        keyboard.add(InlineKeyboardButton("Карта 2", callback_data="tinkoff_card_1"))
    elif bank == "Альфа-Банк":
        keyboard.add(InlineKeyboardButton("Карта 3", callback_data="alfa_card_1"))
    keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_banks"))
    return keyboard

# Обработчик выбора карты
@dp.callback_query_handler(lambda c: c.data.endswith("_card_1"))
async def card_info(callback_query: types.CallbackQuery):
    card_info_text = "Информация о карте..."  # Заглушка, сюда подставим реальные данные
    await bot.send_message(callback_query.from_user.id, card_info_text, reply_markup=apply_button())

# Кнопка "Оформить карту"
def apply_button():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Оформить на лучших условиях", url="https://your-ref-link.com"))
    keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_banks"))
    return keyboard

# Обработчик кнопки "Назад"
@dp.callback_query_handler(lambda c: c.data == "back_to_banks")
async def back_to_banks(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Выбери банк:", reply_markup=banks_keyboard())

# Обработчик вебхука
@app.post(WEBHOOK_PATH)
async def webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.process_update(telegram_update)
    return {"status": "ok"}

# Запуск вебхука
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown():
    await bot.delete_webhook()

if __name__ == "__main__":
    uvicorn.run(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
