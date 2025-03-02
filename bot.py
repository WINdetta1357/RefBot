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
    keyboard.append(("🔙 Назад", "back_main"))

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

    elif query.data == "back_main":
        await start(update, context)
        return ASK_AGE

async def show_card_selection(query):
    """Меню выбора карт"""
    user_id = query.from_user.id
    selected_bank = user_data[user_id]['selected_bank']

    keyboard = []
    for card_name, data in banks[selected_bank].items():
        if user_data[user_id]['age'] >= data['age_limit']:
            is_selected = card_name in user_data[user_id]['selected_cards']
            text = f"{'✅ ' if is_selected else ''}{card_name}"
            keyboard.append((text, f"select_card_{card_name}"))

    keyboard.append(("🔍 Сравнить выбранные", "compare_selected"))
    keyboard.append(("🔙 Назад", "back_bank"))

    await query.edit_message_text(
        f"🔍 Выбери карты в банке {selected_bank}:",
        reply_markup=build_keyboard(keyboard)
    )

async def handle_card_selection(update: Update, context: CallbackContext):
    """Обработка выбора карты"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data.startswith("select_card_"):
        card_name = query.data.split("_", 2)[2]
        
        if card_name in user_data[user_id]['selected_cards']:
            user_data[user_id]['selected_cards'].remove(card_name)
        else:
            user_data[user_id]['selected_cards'].append(card_name)

        await show_card_selection(query)

    elif query.data == "compare_selected":
        await compare_selected_cards(query)

    elif query.data == "back_bank":
        await show_bank_selection(query)
        return SELECT_BANK

async def compare_selected_cards(query):
    """Сравнение карт"""
    user_id = query.from_user.id
    selected = user_data[user_id]['selected_cards']

    if not selected:
        await query.edit_message_text("❌ Выберите карты для сравнения!")
        return

    text = "🔍 <b>Сравнение карт:</b>\n\n"
    for card_name in selected:
        for bank_name, cards in banks.items():
            if card_name in cards:
                data = cards[card_name]
                text += f"🏦 <b>{bank_name}</b> - <b>{card_name}</b>\n"
                text += "🔥 <u>Преимущества:</u>\n- " + "\n- ".join(data["advantages"]) + "\n"
                text += f"🔗 <a href='{data['ref_link']}'>Ссылка на карту</a>\n\n"

    keyboard = [("🔙 Назад", "back_bank")]
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
            SELECT_BANK: [CallbackQueryHandler(handle_bank_selection)],
            SELECT_CARDS: [CallbackQueryHandler(handle_card_selection)]
        },
        fallbacks=[],
        per_user=True,
        per_chat=True,
        per_message=False
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_card_selection, pattern="^select_card_"))
    app.add_handler(CallbackQueryHandler(compare_selected_cards, pattern="^compare_selected$"))

    app.run_polling()

if __name__ == "__main__":
    main()
