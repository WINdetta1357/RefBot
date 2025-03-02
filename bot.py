from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes
)
import logging
import os
from dotenv import load_dotenv
from collections import defaultdict

# --- Настройки ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
    },
    "Сбербанк": {
        "SberPrime": {
            "age_limit": 16,
            "advantages": ["Подписки (Okko, СберПрайм)", "Кэшбэк 10%"],
            "ref_link": "https://sberbank.ru/prime",
            "card_type": ["subscription"]
        }
    }
}

# --- Глобальные переменные ---
user_data = defaultdict(lambda: {
    'age': None,
    'points': 0,
    'achievements': set(),
    'selected_cards': [],
    'invited': 0,
    'preferences': defaultdict(int)
})

ASK_AGE = 1
SELECT_CARDS = 2

# --- Вспомогательные функции ---
def build_keyboard(buttons, back_button=None):
    """Создаёт инлайн-клавиатуру из списка кнопок."""
    keyboard = [[InlineKeyboardButton(btn[0], callback_data=btn[1])] for btn in buttons]
    if back_button:
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=back_button)])
    return InlineKeyboardMarkup(keyboard)

# --- Основные обработчики ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск бота с реферальной системой."""
    args = context.args if context.args else []
    user_id = update.effective_user.id
    
    # Обработка реферальной ссылки
    if args and args[0].startswith("ref_"):
        referrer_id = int(args[0][4:])
        if referrer_id != user_id:
            user_data[referrer_id]['points'] += 50
            user_data[referrer_id]['invited'] += 1
    
    keyboard = [("14-17 лет", "age_14_17"), ("18+ лет", "age_18_plus")]
    await update.message.reply_text(
        "👋 Привет! Я помогу тебе выбрать лучшую банковскую карту!\nВыбери свой возраст:",
        reply_markup=build_keyboard(keyboard)
    )
    return ASK_AGE

async def handle_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора возраста."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user_data[user_id]['age'] = 14 if query.data == "age_14_17" else 18
    user_data[user_id]['points'] += 10
    
    await show_main_menu(query)
    return ConversationHandler.END

async def show_main_menu(query):
    """Главное меню с кнопками."""
    buttons = [("🏦 Карты", "category_banks"), ("🔍 Сравнить", "compare_cards"), 
               ("🎁 Акции", "promo"), ("🏆 Профиль", "profile")]
    await query.edit_message_text(
        "🎮 Главное меню:",
        reply_markup=build_keyboard(buttons)
    )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Профиль пользователя."""
    query = update.callback_query
    user_id = query.from_user.id
    data = user_data[user_id]
    
    text = (f"👤 Ваш профиль:\n\n"
            f"⭐ Баллы: {data['points']}\n"
            f"🏆 Достижения: {len(data['achievements'])}\n"
            f"🤝 Приглашено друзей: {data['invited']}\n")
    
    buttons = [("🔗 Пригласить друзей", "invite"), ("🔙 Назад", "back_main")]
    await query.edit_message_text(text, reply_markup=build_keyboard(buttons))

async def show_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает акции."""
    query = update.callback_query
    await query.answer()
    
    text = "🎁 <b>Специальные предложения:</b>\n\n"
    for bank, cards in banks.items():
        for card, data in cards.items():
            if 'promo' in data:
                text += f"🏦 <b>{bank}</b> - {card}:\n"
                text += "\n".join(f"• {promo}" for promo in data['promo']) + "\n\n"
    
    await query.edit_message_text(text, reply_markup=build_keyboard([], "back_main"), parse_mode="HTML")

async def handle_card_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора карт."""
    query = update.callback_query
    await query.answer()

    if query.data == "back_main":
        await show_main_menu(query)
        return

async def show_card_selection(query, context):
    """Меню выбора карт для сравнения."""
    user_id = query.from_user.id
    keyboard = []

    for bank_name, cards in banks.items():
        for card_name, data in cards.items():
            if user_data[user_id]['age'] >= data['age_limit']:
                keyboard.append([(card_name, f"select_{bank_name}_{card_name}")])

    keyboard.append([("🔙 Назад", "back_main")])
    await query.edit_message_text("🔍 Выбери карты для сравнения:", reply_markup=build_keyboard(keyboard))

# --- Запуск бота ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ASK_AGE: [CallbackQueryHandler(handle_age)]},
        fallbacks=[]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(profile, pattern="^profile$"))
    app.add_handler(CallbackQueryHandler(show_promo, pattern="^promo$"))
    app.add_handler(CallbackQueryHandler(show_main_menu, pattern="^back_main$"))
    
    app.run_polling()

if __name__ == "__main__":
    main()
