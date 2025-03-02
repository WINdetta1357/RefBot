from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
import logging
import os
from dotenv import load_dotenv
from collections import defaultdict

# --- Настройки ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

# --- Данные о картах ---
banks = {
    "Тинькофф": {
        "Тинькофф Блэк": {
            "age_limit": 14,
            "advantages": ["Кэшбэк 1-30%", "До 7% на остаток"],
            "ref_link": "https://tinkoff.ru/black",
            "promo": ["+1000 ₽ за регистрацию"],
            "card_type": ["cashback"]
        },
        "Тинькофф Платинум": {
            "age_limit": 18,
            "advantages": ["Кредитный лимит до 700 000 ₽", "Рассрочка 0%"],
            "ref_link": "https://tinkoff.ru/platinum",
            "card_type": ["credit"]
        }
    }
}

user_data = defaultdict(lambda: {
    'age': None,
    'selected_cards': []
})

ASK_AGE = 1
SELECT_CARDS = 2

# --- Вспомогательная функция для клавиатуры ---
def build_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=callback)] for text, callback in buttons])

# --- Обработчики ---
async def start(update: Update, context: CallbackContext):
    """Запуск бота"""
    keyboard = [
        ("14-17 лет", "age_14_17"),
        ("18+ лет", "age_18_plus")
    ]
    await update.message.reply_text(
        "👋 Привет! Выбери свой возраст:",
        reply_markup=build_keyboard(keyboard)
    )
    return ASK_AGE

async def handle_age(update: Update, context: CallbackContext):
    """Обработка возраста"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data[user_id]['age'] = 14 если query.data == "age_14_17" иначе 18

    # Переход в меню выбора карт
    await show_card_selection(query)
    return SELECT_CARDS

async def show_card_selection(query):
    """Меню выбора карт"""
    user_id = query.from_user.id  # Исправлено получение user_id

    keyboard = []
    for bank_name, cards in banks.items():
        for card_name, data in cards.items():
            if user_data[user_id]['age'] >= data['age_limit']:
                is_selected = card_name in user_data[user_id]['selected_cards']
                text = f"{'✅ ' если is_selected иначе ''}{card_name}"
                keyboard.append((text, f"select_{bank_name}_{card_name}"))

    keyboard.append(("🔍 Сравнить выбранные", "compare_selected"))
    keyboard.append(("🔙 Назад", "back_main"))

    await query.edit_message_text(
        "🔍 Выбери карты для сравнения:",
        reply_markup=build_keyboard(keyboard)
    )

async def handle_card_selection(update: Update, context: CallbackContext):
    """Обработка выбора карты"""
    query = update.callback_query
    await query.answer()

    print("Query Data:", query.data)  # Для отладки

    user_id = query.from_user.id

    если query.data.startswith("select_"):
        _, bank_name, card_name = query.data.split("_", 2)
        
        если card_name in user_data[user_id]['selected_cards']:
            user_data[user_id]['selected_cards'].remove(card_name)
        иначе:
            user_data[user_id]['selected_cards'].append(card_name)

        await show_card_selection(query)

    иначе если query.data == "compare_selected":
        await compare_selected_cards(query)

    иначе если query.data == "back_main":
        await start(update, context)

async def compare_selected_cards(query):
    """Сравнение карт"""
    user_id = query.from_user.id  # Исправлено получение user_id
    selected = user_data[user_id]['selected_cards']

    если not selected:
        await query.edit_message_text("❌ Выберите карты для сравнения!")
        return

    text = "🔍 <b>Сравнение карт:</b>\n\n"
    for card_name in selected:
        for bank_name, cards in banks.items():
            если card_name in cards:
                data = cards[card_name]
                text += f"🏦 <b>{bank_name}</b> - <b>{card_name}</b>\n"
                text += "🔥 <u>Преимущества:</u>\n- " + "\n- ".join(data["advantages"]) + "\n\n"

    keyboard = [("🔙 Назад", "category_banks")]
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )

# --- Запуск бота ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_AGE: [CallbackQueryHandler(handle_age)],
            SELECT_CARDS: [CallbackQueryHandler(handle_card_selection)]
        },
        fallbacks=[],
        per_user=True,
        per_chat=True,
        per_message=False
    )

    app.add_handler(conv_handler)
    app.add_handler
