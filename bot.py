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

# --- Данные о банках и картах ---
banks = {
    "СберБанк": {
        "СберКарта": {
            "age_limit": 14,
            "advantages": ["Кэшбэк до 10%", "Бесплатное обслуживание"],
            "ref_link": "https://www.sberbank.ru/ru/person/bank_cards/debet/sbercard"
        },
        "Кредитная карта СберБанк": {
            "age_limit": 18,
            "advantages": ["Кредитный лимит до 300 000 ₽", "Льготный период до 50 дней"],
            "ref_link": "https://www.sberbank.ru/ru/person/bank_cards/credit/credit_card"
        }
    },
    "Альфа-Банк": {
        "Альфа-Карта": {
            "age_limit": 14,
            "advantages": ["Кэшбэк до 5%", "Бесплатное обслуживание"],
            "ref_link": "https://alfabank.ru/get-money/credit-cards/alfa-card/"
        },
        "Кредитная карта Альфа-Банк": {
            "age_limit": 18,
            "advantages": ["Кредитный лимит до 500 000 ₽", "Льготный период до 100 дней"],
            "ref_link": "https://alfabank.ru/get-money/credit-cards/100-days/"
        }
    },
    "Тинькофф": {
        "Тинькофф Блэк": {
            "age_limit": 14,
            "advantages": ["Кэшбэк 1-30%", "До 7% на остаток"],
            "ref_link": "https://tinkoff.ru/cards/debit-cards/tinkoff-black/"
        },
        "Тинькофф Платинум": {
            "age_limit": 18,
            "advantages": ["Кредитный лимит до 700 000 ₽", "Рассрочка 0%"],
            "ref_link": "https://tinkoff.ru/cards/credit-cards/tinkoff-platinum/"
        }
    }
}

user_data = defaultdict(lambda: {
    'age': None,
    'selected_bank': None,
    'selected_cards': []
})

ASK_AGE = 1
SELECT_BANK = 2
SELECT_CARDS = 3
COMPARE_CARDS = 4

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
    user_data[user_id]['age'] = 14 if query.data == "age_14_17" else 18

    # Переход в меню выбора банка
    await show_bank_selection(query)
    return SELECT_BANK

async def show_bank_selection(query):
    """Меню выбора банка"""
    user_id = query.from_user.id

    keyboard = [(bank_name, f"select_bank_{bank_name}") for bank_name in banks.keys()]
    keyboard.append(("🔍 Сравнить все карты", "compare_all_cards"))
    keyboard.append(("🔙 Назад", "back_age"))

    await query.edit_message_text(
        "🏦 Выбери банк:",
        reply_markup=build_keyboard(keyboard)
    )

async def handle_bank_selection(update: Update, context: CallbackContext):
    """Обработка выбора банка"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data.startswith("select_bank_"):
        bank_name = query.data.split("_", 2)[2]
        user_data[user_id]['selected_bank'] = bank_name

        # Переход в меню выбора карт
        await show_card_selection(query)
        return SELECT_CARDS

    elif query.data == "compare_all_cards":
        await compare_all_cards(query)
        return COMPARE_CARDS

    elif query.data == "back_age
