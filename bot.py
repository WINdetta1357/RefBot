import sqlite3
from urllib.parse import urlparse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import URLInputFile

# Инициализация бота
bot = Bot(token="YOUR_BOT_TOKEN")
dp = Dispatcher()

# Настройка базы данных
conn = sqlite3.connect('cards.db')
cursor = conn.cursor()

# Список администраторов
ADMINS = [123456789]  # Замените на ваш ID

# Валидация URL
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

# Инициализация БД
def init_db():
    with conn:
        cursor.execute('''CREATE TABLE IF NOT EXISTS cards
                       (id INTEGER PRIMARY KEY,
                        name TEXT UNIQUE,
                        cashback REAL,
                        limits TEXT,
                        insurance TEXT,
                        category TEXT)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS links
                       (card_id INTEGER PRIMARY KEY,
                        url TEXT,
                        FOREIGN KEY(card_id) REFERENCES cards(id))''')

# Главное меню
main_kb = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🎮 Геймификация")],
        [types.KeyboardButton(text="💳 Сравнить карты")],
        [types.KeyboardButton(text="📚 Обучение")]
    ],
    resize_keyboard=True
)

# Обработчики команд
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🏦 Добро пожаловать в финансового помощника!\n"
        "Выберите действие:",
        reply_markup=main_kb
    )

@dp.message(Command("addlink"))
async def add_link(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("⛔ Доступ запрещен")
    
    await message.answer(
        "🔗 Введите данные в формате:\n"
        "<b>Название карты | Ссылка</b>\n"
        "Пример: Tinkoff Black | https://tinkoff.ru/black",
        parse_mode="HTML"
    )

@dp.message(F.text.contains("|"))
async def process_link(message: types.Message):
    try:
        card_name, url = message.text.split("|", 1)
        card_name = card_name.strip()
        url = url.strip()
        
        if not is_valid_url(url):
            return await message.answer("❌ Некорректная ссылка!")
        
        with conn:
            cursor.execute("SELECT id FROM cards WHERE name=?", (card_name,))
            card_id = cursor.fetchone()
            
            if card_id:
                cursor.execute(
                    "INSERT OR REPLACE INTO links VALUES (?, ?)",
                    (card_id[0], url)
                )
                await message.answer(f"✅ Ссылка для {card_name} обновлена!")
            else:
                await message.answer("❌ Карта не найдена в базе")
                
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)}")

@dp.message(F.text == "💳 Сравнить карты")
async def show_cards(message: types.Message):
    try:
        cursor.execute('''SELECT cards.*, links.url 
                       FROM cards 
                       LEFT JOIN links ON cards.id=links.card_id''')
        
        cards = cursor.fetchall()
        
        if not cards:
            return await message.answer("📭 База карт пуста")
            
        for card in cards:
            card_id, name, cashback, limits, insurance, category, url = card
            
            builder = InlineKeyboardBuilder()
            if url:
                builder.add(types.InlineKeyboardButton(
                    text="🚀 Оформить карту",
                    url=url
                ))
            
            builder.add(types.InlineKeyboardButton(
                text="⭐ Добавить в избранное",
                callback_data=f"fav_{card_id}"
            ))
            
            text = (
                f"🏦 <b>{name}</b>\n\n"
                f"💵 Кэшбек: {cashback}%\n"
                f"📊 Лимиты: {limits}\n"
                f"🛡 Страховки: {insurance}\n"
                f"📁 Категория: {category}"
            )
            
            await message.answer_photo(
                photo=URLInputFile("https://example.com/card-image.jpg"),
                caption=text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)}")

# Запуск приложения
if __name__ == "__main__":
    init_db()
    print("Бот запущен!")
    dp.run_polling(bot)
