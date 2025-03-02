import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import URLInputFile

bot = Bot(token="YOUR_BOT_TOKEN")
dp = Dispatcher()

# Инициализация БД
conn = sqlite3.connect('cards.db')
cursor = conn.cursor()

# Создание таблиц
cursor.execute('''CREATE TABLE IF NOT EXISTS cards
               (id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                cashback REAL,
                limits TEXT,
                insurance TEXT,
                category TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS links
               (card_id INTEGER,
                url TEXT,
                FOREIGN KEY(card_id) REFERENCES cards(id))''')

conn.commit()

# Список админов (можно вынести в отдельную таблицу)
ADMINS = [123456789]

# Клавиатура для главного меню
main_kb = [
    [types.KeyboardButton(text="🎮 Геймификация")],
    [types.KeyboardButton(text="💳 Сравнить карты")],
    [types.KeyboardButton(text="📚 Обучение")]
]

# Обработчики команд
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Добро пожаловать в финансового помощника!",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=main_kb,
            resize_keyboard=True
        )
    )

# Добавление ссылок (только для админов)
@dp.message(Command("addlink"))
async def add_link(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("Доступ запрещен")
    
    await message.answer(
        "Введите данные в формате:\n"
        "Название карты | Ссылка\n"
        "Пример: Tinkoff Black | https://tinkoff.ru/black"
    )
    
@dp.message(F.text.contains("|"))
async def process_link(message: types.Message):
    try:
        card_name, url = message.text.split("|", 1)
        card_name = card_name.strip()
        url = url.strip()
        
        # Получаем ID карты
        cursor.execute("SELECT id FROM cards WHERE name=?", (card_name,))
        card_id = cursor.fetchone()
        
        if card_id:
            # Обновляем или добавляем ссылку
            cursor.execute(
                "INSERT OR REPLACE INTO links VALUES (?, ?)",
                (card_id[0], url)
            conn.commit()
            await message.answer(f"Ссылка для {card_name} обновлена!")
        else:
            await message.answer("Карта не найдена в базе")
            
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")

# Показ карт с кнопками
@dp.message(F.text == "💳 Сравнить карты")
async def show_cards(message: types.Message):
    cursor.execute('''SELECT cards.*, links.url 
                   FROM cards 
                   LEFT JOIN links ON cards.id=links.card_id''')
    
    cards = cursor.fetchall()
    
    for card in cards:
        card_id, name, cashback, limits, insurance, category, url = card
        
        text = (
            f"<b>{name}</b>\n\n"
            f"Кэшбек: {cashback}%\n"
            f"Лимиты: {limits}\n"
            f"Страховки: {insurance}\n"
            f"Категория: {category}"
        )
        
        # Создаем клавиатуру
        builder = InlineKeyboardBuilder()
        if url:
            builder.add(types.InlineKeyboardButton(
                text="🚀 Оформить карту",
                url=url)
            )
            
        builder.add(types.InlineKeyboardButton(
            text="⭐ Добавить в избранное",
            callback_data=f"fav_{card_id}")
        )
        
        await message.answer_photo(
            photo=URLInputFile("https://example.com/card-image.jpg"),
            caption=text,
            reply_markup=builder.as_markup()
        )

# Запуск бота
if __name__ == "__main__":
    dp.run_polling(bot)
