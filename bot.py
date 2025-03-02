from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
import logging
import os
from dotenv import load_dotenv

# --- Настройки ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "8105012250:AAFmOW45SKDGrn0pqIFvSVhQv3uwodCMKXs")

# --- Данные о картах ---
banks = {
    "Тинькофф": {
        "Тинькофф Блэк": {
            "age_limit": 14,
            "advantages": ["Кэшбэк 1-30%", "До 7% на остаток"],
            "ref_link": "https://tinkoff.ru/black",
            "promo": ["+1000 ₽ за регистрацию"]
        },
        "Тинькофф Платинум": {
            "age_limit": 18,
            "advantages": ["Кредитный лимит до 700 000 ₽", "Рассрочка 0%"],
            "ref_link": "https://tinkoff.ru/platinum"
        }
    },
    "Сбербанк": {
        "SberPrime": {
            "age_limit": 16,
            "advantages": ["Подписки (Okko, СберПрайм)", "Кэшбэк 10%"],
            "ref_link": "https://sberbank.ru/prime"
        }
    }
}

# --- Глобальные переменные ---
user_age = {}
ASK_AGE = 1

# --- Основные функции ---
async def start(update: Update, context: CallbackContext):
    """Запуск бота и запрос возраста"""
    keyboard = [
        [InlineKeyboardButton("14-17 лет", callback_data="age_14_17")],
        [InlineKeyboardButton("18+ лет", callback_data="age_18_plus")]
    ]
    await update.message.reply_text(
        "👋 Привет! Я твой бот. Выбери свой возраст:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_AGE

async def handle_age(update: Update, context: CallbackContext):
    """Обработка выбора возраста"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if query.data == "age_14_17":
        user_age[chat_id] = 14
    else:
        user_age[chat_id] = 18

    await show_main_menu(query)
    return ConversationHandler.END

async def show_main_menu(query):
    """Главное меню с кнопками"""
    keyboard = [
        [InlineKeyboardButton("🏦 Банковские карты", callback_data="category_banks")],
        [InlineKeyboardButton("🔍 Сравнить карты", callback_data="compare_cards")],
        [InlineKeyboardButton("🎁 Акции", callback_data="promo")]
    ]
    await query.edit_message_text(
        "🎮 Выбери раздел:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: CallbackContext):
    """Обработка нажатия кнопок"""
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "category_banks":
            keyboard = [[InlineKeyboardButton(bank, callback_data=f"bank_{bank}")] for bank in banks]
            await query.edit_message_text("🏦 Выбери банк:", reply_markup=InlineKeyboardMarkup(keyboard))

        elif query.data.startswith("bank_"):
            bank_name = query.data.split("_")[1]
            chat_id = query.message.chat_id
            keyboard = []
            for card in banks[bank_name]:
                if user_age.get(chat_id, 0) >= banks[bank_name][card]["age_limit"]:
                    keyboard.append([InlineKeyboardButton(card, callback_data=f"card_{bank_name}_{card}")])
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="category_banks")])
            await query.edit_message_text(f"📇 Карты {bank_name}:", reply_markup=InlineKeyboardMarkup(keyboard))

        elif query.data.startswith("card_"):
            _, bank_name, card_name = query.data.split("_")
            card = banks[bank_name][card_name]
            text = f"<b>{card_name}</b>\n\n"
            text += "🔥 <u>Преимущества</u>:\n- " + "\n- ".join(card["advantages"]) + "\n\n"
            text += f"🔗 <a href='{card['ref_link']}'>Оформить карту</a>"
            await query.edit_message_text(text, parse_mode="HTML")

        elif query.data == "compare_cards":
            text = "🔍 <b>Сравнение карт:</b>\n\n"
            for bank_name, cards in banks.items():
                text += f"🏦 <u>{bank_name}</u>:\n"
                for card_name, data in cards.items():
                    text += f"▫️ {card_name} (от {data['age_limit']}+ лет)\n"
            await query.edit_message_text(text, parse_mode="HTML")

        elif query.data == "promo":
            text = "🎁 <b>Акции:</b>\n\n"
            for bank_name, cards in banks.items():
                for card_name, data in cards.items():
                    if "promo" in data:
                        text += f"🔥 {card_name}: {', '.join(data['promo'])}\n"
            await query.edit_message_text(text, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await query.message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")

def main():
    """Запуск бота"""
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={ASK_AGE: [CallbackQueryHandler(handle_age)]},
        fallbacks=[],
        per_message=True
    )
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))

    # Для Railway
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://web-production-c568.up.railway.app/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
