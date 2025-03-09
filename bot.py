import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes
from dotenv import load_dotenv

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка токена из переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Состояния диалога
MAIN_MENU, BANK_SELECTION, CARD_SELECTION, ALL_CARDS_VIEW = range(4)

# Данные о банках, картах и изображениях
banks = {
    "СберБанк": {
        "СберКарта": {
            "age_limit": 14,
            "advantages": ["Кэшбэк до 10%", "Бесплатное обслуживание"],
            "ref_link": "https://example.com/sber",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/2/2f/SberCard.png"
        },
        "Кредитная карта": {
            "age_limit": 18,
            "advantages": ["Льготный период 50 дней", "Лимит до 500 000 ₽"],
            "ref_link": "https://example.com/sber_credit",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/c/cf/SberCreditCard.png"
        }
    },
    "Тинькофф": {
        "Тинькофф Блэк": {
            "age_limit": 14,
            "advantages": ["До 30% кэшбэка", "Инвестиции"],
            "ref_link": "https://example.com/tinkoff",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/e3/Tinkoff_Black.png"
        },
        "Тинькофф Платинум": {
            "age_limit": 18,
            "advantages": ["Рассрочка 0%", "Премиальное обслуживание"],
            "ref_link": "https://example.com/tinkoff_platinum",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/3/3b/Tinkoff_Platinum.png"
        }
    }
}

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("14-17 лет", callback_data="age_14_17")],
        [InlineKeyboardButton("18+ лет", callback_data="age_18_plus")]
    ]
    await update.message.reply_text(
        "👋 Добро пожаловать! Выберите ваш возраст:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MAIN_MENU

# Обработчик выбора возраста
async def handle_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["age"] = 14 if query.data == "age_14_17" else 18
    return await show_bank_selection(query)

# Показ списка банков
async def show_bank_selection(query) -> int:
    await query.answer()
    keyboard = [[InlineKeyboardButton(bank, callback_data=f"bank_{bank}")] for bank in banks] + [
        [InlineKeyboardButton("Все карты", callback_data="show_all_cards")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    await query.edit_message_text("🏦 Выберите банк:", reply_markup=InlineKeyboardMarkup(keyboard))
    return BANK_SELECTION

# Обработчик выбора карты
async def handle_card_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    bank_name = context.user_data.get("current_bank")
    card_name = query.data.split("_", 1)[1]
    card_info = banks[bank_name][card_name]

    text = f"🏦 {bank_name} - {card_name}\n\n"
    text += "🔥 Преимущества:\n" + "\n".join(f"• {adv}" for adv in card_info["advantages"])

    keyboard = [[InlineKeyboardButton("💳 Оформить карту", url=card_info["ref_link"])]],
    keyboard += [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_cards")], [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]

    await query.message.reply_photo(
        photo=card_info["image_url"],
        caption=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CARD_SELECTION

# Основная функция
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(handle_age)],
            BANK_SELECTION: [CallbackQueryHandler(show_bank_selection)],
            CARD_SELECTION: [CallbackQueryHandler(handle_card_selection)]
        },
        fallbacks=[],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
