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
BOT_TOKEN = os.getenv("BOT_TOKEN", "8105012250:AAFmOW45SKDGrn0pqIFvSVhQv3uwodCMKXs")  # Токен бота

# --- Данные о картах ---
banks = {
    "Тинькофф": {
        "Тинькофф Блэк": {
            "age_limit": 14,
            "advantages": ["Кэшбэк 1-30%", "До 7% на остаток"],
            "ref_link": "https://tinkoff.ru/black"
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
        reply_markup=InlineKeyboardMarkup(keyboard))
    return ASK_AGE

async def handle_age(update: Update, context: CallbackContext):
    """Обработка выбора возраста"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    # Сохраняем возраст
    if query.data == "age_14_17":
        user_age[chat_id] = 14
    else:
        user_age[chat_id] = 18

    # Показываем главное меню
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
        reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: CallbackContext):
    """Обработка нажатия кнопок"""
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "category_banks":
            # Показываем список банков
            keyboard = [[InlineKeyboardButton(bank, callback_data=f"bank_{bank}")] for bank in banks]
            await query.edit_message_text("🏦 Выбери банк:", reply_markup=InlineKeyboardMarkup(keyboard))

        elif query.data.startswith("bank_"):
            # Показываем карты выбранного банка
            bank_name = query.data.split("_")[1]
            chat_id = query.message.chat_id
            keyboard = []
            for card in banks[bank_name]:
                if user_age.get(chat_id, 0) >= banks[bank_name][card]["age_limit"]:
                    keyboard.append([InlineKeyboardButton(card, callback_data=f"card_{bank_name}_{card}")])
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="category_banks")])
            await query.edit_message_text(f"📇 Карты {bank_name}:", reply_markup=InlineKeyboardMarkup(keyboard))

        elif query.data == "compare_cards":
            # Сравнение всех карт
            text = "🔍 **Сравнение условий:**\n\n"
            for bank in banks.values():
                for card_name, data in bank.items():
                    text += f"▫️ **{card_name}**\n— Возраст: {data['age_limit']}+\n— Преимущества: {', '.join(data['advantages'])}\n\n"
            await query.edit_message_text(text, parse_mode="Markdown")

        elif query.data == "promo":
            # Показываем акции
            text = "🎁 **Акции и спецпредложения:**\n\n"
            for bank in banks.values():
                for card in bank.values():
                    if "promo" in card:
                        text += f"🔥 {', '.join(card['promo'])}\n"
            await query.edit_message_text(text, parse_mode="Markdown")

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
        fallbacks=[]
    )
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))

    # Для облачного хостинга (Railway/Heroku)
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://ваш-домен.xyz/{BOT_TOKEN}"  # Замените на реальный URL!
    )

if __name__ == "__main__":
    main()
