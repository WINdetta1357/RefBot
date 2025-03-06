from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, CallbackContext
import logging
import os
from dotenv import load_dotenv

# --- Настройки ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

# --- Константы для состояний ---
ASK_AGE = 1
SELECT_BANK = 2
SELECT_CARDS = 3
SHOW_ALL_CARDS = 4

# --- Данные о банках ---
banks = {
    "СберБанк": {
        "СберКарта": {
            "age_limit": 14,
            "advantages": ["Кэшбэк до 10%", "Бесплатное обслуживание"],
            "ref_link": "https://unicom24.ru/redirect/1300139"
        },
        "Кредитная карта СберБанк": {
            "age_limit": 18,
            "advantages": ["Кредитный лимит до 300 000 ₽", "Льготный период до 50 дней"],
            "ref_link": "https://unicom24.ru/redirect/1300140"
        }
    },
    "Тинькофф": {
        "Тинькофф Блэк": {
            "age_limit": 14,
            "advantages": ["Кэшбэк 1-30%", "До 7% на остаток"],
            "ref_link": "https://unicom24.ru/redirect/1300141"
        },
        "Тинькофф Платинум": {
            "age_limit": 18,
            "advantages": ["Кредитный лимит до 700 000 ₽", "Рассрочка 0%"],
            "ref_link": "https://unicom24.ru/redirect/1300142"
        }
    }
}

user_data = {}

# --- Вспомогательные функции ---
def build_keyboard(buttons):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text, callback_data=callback)] for text, callback in buttons]
    )

# --- Обработчики ---
async def start(update: Update, context: CallbackContext):
    """Главное меню"""
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
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    age = 14 if query.data == "age_14_17" else 18
    user_data[user_id] = {"age": age}

    return await show_banks_menu(query)

async def show_banks_menu(query):
    """Меню выбора банка"""
    keyboard = [(bank, f"select_bank_{bank}") for bank in banks.keys()]
    keyboard.append(("Показать все карты", "show_all_cards"))
    keyboard.append(("🔙 Назад", "back_to_main_menu"))

    await query.edit_message_text(
        "🏦 Выбери банк или посмотри условия всех карт:",
        reply_markup=build_keyboard(keyboard)
    )
    return SELECT_BANK

async def handle_bank_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "show_all_cards":
        return await show_all_cards(query)

    bank_name = query.data.split("_", 2)[2]
    user_data[user_id]['selected_bank'] = bank_name

    return await show_cards_menu(query, bank_name)

async def show_cards_menu(query, bank_name):
    """Меню выбора карт в конкретном банке"""
    keyboard = [(card, f"show_card_{card}") for card in banks[bank_name].keys()]
    keyboard.append(("🔙 Назад", "back_to_banks"))

    await query.edit_message_text(
        f"🔍 Выбери карту в банке {bank_name}:",
        reply_markup=build_keyboard(keyboard)
    )
    return SELECT_CARDS

async def show_all_cards(query):
    """Показать условия всех карт"""
    text = "🔍 <b>Условия всех карт:</b>\n\n"
    for bank_name, cards in banks.items():
        for card_name, card in cards.items():
            text += f"🏦 <b>{bank_name}</b> - <b>{card_name}</b>\n"
            text += "🔥 <u>Преимущества:</u>\n- " + "\n- ".join(card["advantages"]) + "\n"
            text += f"🔗 <a href='{card['ref_link']}'>Ссылка на карту</a>\n\n"

    keyboard = [("🔙 Назад", "back_to_banks")]
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
    return SELECT_BANK

async def handle_card_info(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    bank_name = user_data[user_id]['selected_bank']
    card_name = query.data.split("_", 2)[2]
    card = banks[bank_name][card_name]

    text = f"🏦 <b>{bank_name}</b> - <b>{card_name}</b>\n\n"
    text += "🔥 <u>Преимущества:</u>\n- " + "\n- ".join(card["advantages"]) + "\n\n"

    keyboard = [[InlineKeyboardButton("Оформить", url=card['ref_link'])]]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_banks")])
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SELECT_CARDS

async def handle_back(update: Update, context: CallbackContext):
    """Обработка возвратов"""
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_main_menu":
        return await start(update, context)
    elif query.data == "back_to_banks":
        return await show_banks_menu(query)
    elif query.data == "back_to_cards":
        user_id = query.from_user.id
        return await show_cards_menu(query, user_data[user_id]['selected_bank'])

async def error_handler(update: object, context: CallbackContext) -> None:
    """Обработчик ошибок"""
    logging.error("Exception occurred", exc_info=context.error)

# --- Запуск приложения ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_AGE: [CallbackQueryHandler(handle_age)],
            SELECT_BANK: [
                CallbackQueryHandler(handle_bank_selection),
                CallbackQueryHandler(handle_back, pattern="back_to_main_menu")
            ],
            SELECT_CARDS: [
                CallbackQueryHandler(handle_card_info),
                CallbackQueryHandler(handle_back, pattern="back_to_banks")
            ],
            SHOW_ALL_CARDS: [CallbackQueryHandler(show_all_cards)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
