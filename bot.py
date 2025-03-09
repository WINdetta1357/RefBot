import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes
from dotenv import load_dotenv

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelень)s - %(сообщение)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка токена из переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Состояния диалога
MAIN_MENU, BANK_SELECTION, CARD_SELECTION, ALL_CARDS_VIEW = range(4)

# Данные о банках и картах
banks = {
    "СберБанк": {
        "СберКарта": {
            "age_limit": 14,
            "advantages": ["Кэшбэк до 10%", "Бесплатное обслуживание"],
            "ref_link": "https://example.com/sber"
        },
        "Кредитная карта": {
            "age_limit": 18,
            "advantages": ["Льготный период 50 дней", "Лимит до 500 000 ₽"],
            "ref_link": "https://example.com/sber_credit"
        }
    },
    "Тинькофф": {
        "Тинькофф Блэк": {
            "age_limit": 14,
            "advantages": ["До 30% кэшбэка", "Инвестиции"],
            "ref_link": "https://example.com/tinkoff"
        },
        "Тинькофф Платинум": {
            "age_limit": 18,
            "advantages": ["Рассрочка 0%", "Премиальное обслуживание"],
            "ref_link": "https://example.com/tinkoff_platinum"
        }
    }
}

# Вспомогательная функция для создания клавиатуры
def build_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("🎂 14-17 лет", callback_data="age_14_17")],
        [InlineKeyboardButton("🎂 18+ лет", callback_data="age_18_plus")]
    ]
    await update.message.reply_text(
        "👋 <b>Добро пожаловать!</b>\n\nПожалуйста, выберите вашу возрастную категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return MAIN_MENU

# Обработчик выбора возраста
async def handle_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    age_group = query.data
    context.user_data["age"] = 14 if age_group == "age_14_17" else 18
    
    return await show_bank_selection(query)

# Показ списка банков
async def show_bank_selection(query) -> int:
    await query.answer()
    keyboard = [
        [InlineKeyboardButton(bank, callback_data=f"bank_{bank}")] for bank in banks
    ] + [
        [InlineKeyboardButton("📋 Все карты", callback_data="show_all_cards")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    await query.edit_message_text(
        "🏦 <b>Выберите банк:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return BANK_SELECTION

# Обработчик выбора банка
async def handle_bank_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_all_cards":
        return await show_all_cards_view(query)
    
    if query.data == "main_menu":
        return await return_to_main_menu(query)
    
    bank_name = query.data.split("_", 1)[1]
    context.user_data["current_bank"] = bank_name
    
    return await show_card_selection(query, bank_name)

# Показ списка карт выбранного банка
async def show_card_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    cards = banks[context.user_data["current_bank"]]
    keyboard = [
        [InlineKeyboardButton(card, callback_data=f"card_{card}")] for card in cards
    ] + [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_banks")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    await query.edit_message_text(
        f"🏦 <b>{context.user_data['current_bank']}</b>\n\nВыберите карту:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return CARD_SELECTION

# Обработчик выбора карты
async def handle_card_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if "current_bank" not in context.user_data:
        return await return_to_main_menu(query)
    
    card_name = query.data.split("_", 1)[1]
    bank_name = context.user_data["current_bank"]
    card_info = banks[bank_name][card_name]
    
    text = f"🏦 <b>{bank_name}</b> - <b>{card_name}</b>\n\n"
    text += "🔥 <b>Преимущества:</b>\n" + "\n".join(f"• {adv}" for adv in card_info["advantages"])
    text += f"\n\n🔗 <a href='{card_info['ref_link']}'>Ссылка на карту</a>"
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_cards")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return CARD_SELECTION

# Показ всех доступных карт
async def show_all_cards_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    text = "📋 <b>Все доступные карты:</b>\n\n"
    for bank, cards in banks.items():
        text += f"🏦 <b>{bank}</b>:\n"
        for card, info in cards.items():
            text += f"  • {card} ({info['age_limit']}+)\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_banks")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return ALL_CARDS_VIEW

# Обработчик навигации
async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if "current_bank" not in context.user_data:
        return await return_to_main_menu(query)
    
    if query.data == "main_menu":
        return await return_to_main_menu(query)
    
    if query.data == "back_to_banks":
        return await show_bank_selection(query)
    
    if query.data == "back_to_cards":
        return await show_card_selection(query, context.user_data["current_bank"])

# Возврат в главное меню
async def return_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🎂 14-17 лет", callback_data="age_14_17")],
        [InlineKeyboardButton("🎂 18+ лет", callback_data="age_18_plus")]
    ]
    await query.edit_message_text(
        "🏠 <b>Вы вернулись в главное меню!</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return MAIN_MENU

# Завершение сессии
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🚫 Сессия завершена")
    return ConversationHandler.END

# Основная функция
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(handle_age)
            ],
            BANK_SELECTION: [
                CallbackQueryHandler(handle_bank_selection),
                CallbackQueryHandler(return_to_main_menu, pattern="^main_menu$")
            ],
            CARD_SELECTION: [
                CallbackQueryHandler(handle_card_selection),
                CallbackQueryHandler(handle_navigation)
            ],
            ALL_CARDS_VIEW: [
                CallbackQueryHandler(handle_navigation)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
