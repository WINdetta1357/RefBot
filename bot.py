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

# --- Система достижений ---
ACHIEVEMENTS = {
    'first_card': {'name': '🎖 Первая карта', 'desc': 'Выбрать первую карту', 'check': lambda data: len(data['selected_cards']) >= 1},
    'comparer': {'name': '🔍 Сравнитель', 'desc': 'Сравнить 3 карты', 'check': lambda data: len(data['selected_cards']) >= 3},
    'inviter': {'name': '🤝 Посредник', 'desc': 'Пригласить 5 друзей', 'check': lambda data: data['invited'] >= 5},
    'pro': {'name': '💎 Профи', 'desc': 'Заработать 100 баллов', 'check': lambda data: data['points'] >= 100}
}

# --- Вспомогательные функции ---
async def update_achievements(user_id, context):
    """Проверяет и обновляет достижения пользователя."""
    achievements = []
    for ach_id, ach in ACHIEVEMENTS.items():
        if ach_id not in user_data[user_id]['achievements'] and ach['check'](user_data[user_id]):
            user_data[user_id]['achievements'].add(ach_id)
            achievements.append(ach['name'])
    
    if achievements:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 Новое достижение: {', '.join(achievements)}!"
        )

def build_keyboard(buttons, back_button=None):
    """Создаёт инлайн-клавиатуру из списка кнопок."""
    keyboard = []
    for button_row in buttons:
        row = []
        for btn in button_row:
            if isinstance(btn, tuple):
                # Кортеж (текст, callback_data)
                row.append(InlineKeyboardButton(btn[0], callback_data=btn[1]))
            else:
                # Простая строка
                row.append(InlineKeyboardButton(btn, callback_data=btn))
        keyboard.append(row)
    
    if back_button:
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=back_button)])
    
    return InlineKeyboardMarkup(keyboard)

# --- Основные обработчики ---
async def start(update: Update, context: CallbackContext):
    """Запуск бота с реферальной системой."""
    args = context.args
    user_id = update.effective_user.id
    
    # Обработка реферальной ссылки
    if args and args[0].startswith('ref_'):
        referrer_id = int(args[0][4:])
        if referrer_id != user_id:
            user_data[referrer_id]['points'] += 50
            user_data[referrer_id]['invited'] += 1
            await update_achievements(referrer_id, context)
    
    keyboard = [
        [("14-17 лет", "age_14_17")],
        [("18+ лет", "age_18_plus")]
    ]
    await update.message.reply_text(
        "👋 Привет! Я помогу тебе выбрать лучшую банковскую карту!\nВыбери свой возраст:",
        reply_markup=build_keyboard(keyboard)
    )
    return ASK_AGE

async def handle_age(update: Update, context: CallbackContext):
    """Обработка выбора возраста."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user_data[user_id]['age'] = 14 if query.data == "age_14_17" else 18
    user_data[user_id]['points'] += 10  # Начисление баллов за начало работы
    
    await show_main_menu(query)
    return ConversationHandler.END

async def show_main_menu(query):
    """Главное меню с кнопками."""
    buttons = [
        [("🏦 Карты", "category_banks")],
        [("🔍 Сравнить", "compare_cards")],
        [("🎁 Акции", "promo")],
        [("🏆 Профиль", "profile")]
    ]
    await query.edit_message_text(
        "🎮 Главное меню:",
        reply_markup=build_keyboard(buttons)
    )

async def profile(update: Update, context: CallbackContext):
    """Профиль пользователя с достижениями."""
    query = update.callback_query
    user_id = query.from_user.id
    data = user_data[user_id]
    
    text = f"👤 Ваш профиль:\n\n"
    text += f"⭐ Баллы: {data['points']}\n"
    text += f"🏆 Достижения: {len(data['achievements'])}/{len(ACHIEVEMENTS)}\n"
    text += f"🤝 Приглашено друзей: {data['invited']}\n\n"
    
    if data['achievements']:
        text += "Ваши достижения:\n" + "\n".join(
            [ACHIEVEMENTS[ach_id]['name'] for ach_id in data['achievements']]
        )
    
    buttons = [
        [("🔗 Пригласить друзей", "invite")],
        [("📈 Топ пользователей", "leaderboard")],
        [("🔙 Назад", "back_main")]
    ]
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(buttons)
    )

async def show_promo(update: Update, context: CallbackContext):
    """Показывает акции и специальные предложения."""
    query = update.callback_query
    await query.answer()
    
    text = "🎁 <b>Специальные предложения:</b>\n\n"
    for bank_name, cards in banks.items():
        for card_name, data in cards.items():
            if 'promo' in data:
                text += f"🏦 <b>{bank_name}</b> - {card_name}:\n"
                text += "\n".join(f"• {promo}" for promo in data['promo']) + "\n\n"
    
    buttons = [[InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )

async def handle_card_selection(update: Update, context: CallbackContext):
    """Обработка выбора карт для сравнения."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data.startswith("select_"):
        _, bank_name, card_name = query.data.split("_", 2)
        if card_name in user_data[user_id]['selected_cards']:
            user_data[user_id]['selected_cards'].remove(card_name)
        else:
            user_data[user_id]['selected_cards'].append(card_name)
            user_data[user_id]['points'] += 20  # Баллы за выбор карты
            # Обновляем предпочтения
            for card_type in banks[bank_name][card_name].get('card_type', []):
                user_data[user_id]['preferences'][card_type] += 1
            await update_achievements(user_id, context)
        
        await show_card_selection(query)
    
    elif query.data == "compare_selected":
        await compare_selected_cards(query)
        user_data[user_id]['points'] += 30  # Баллы за сравнение
        await update_achievements(user_id, context)

    elif query.data == "back_main":
        await show_main_menu(query)
        return ConversationHandler.END

async def show_card_selection(query):
    """Показывает меню выбора карт для сравнения."""
    user_id = query.message.chat_id
    keyboard = []
    for bank_name, cards in banks.items():
        for card_name, data in cards.items():
            if user_data[user_id]['age'] >= data['age_limit']:
                is_selected = card_name in user_data[user_id]['selected_cards']
                text = f"{'✅ ' if is_selected else ''}{card_name}"
                keyboard.append([InlineKeyboardButton(text, callback_data=f"select_{bank_name}_{card_name}")])
    keyboard.append([InlineKeyboardButton("🔍 Сравнить выбранные", callback_data="compare_selected")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_main")])
    await query.edit_message_text(
        "🔍 Выбери карты для сравнения:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def compare_selected_cards(query):
    """Сравнивает выбранные карты."""
    user_id = query.message.chat_id
    selected = user_data[user_id]['selected_cards']
    
    if not selected:
        await query.edit_message_text("❌ Выберите карты для сравнения!")
        return
    
    text = "🔍 <b>Сравнение карт:</b>\n\n"
    for card_name in selected:
        for bank_name, cards in banks.items():
            if card_name in cards:
                data = cards[card_name]
                text += f"▫️ <b>{card_name}</b> (от {data['age_limit']}+ лет)\n"
                text += "🔥 <u>Преимущества</u>:\n- " + "\n- ".join(data["advantages"]) + "\n\n"
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="compare_cards")]]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# --- Запуск бота ---
def main():
    """Запуск бота."""
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_AGE: [CallbackQueryHandler(handle_age)],
            SELECT_CARDS: [CallbackQueryHandler(handle_card_selection)]
        },
        fallbacks=[],
        per_message=True  # Включена обработка для каждого сообщения
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(profile, pattern="^profile$"))
    app.add_handler(CallbackQueryHandler(show_promo, pattern="^promo$"))
    
    # Для Railway
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://web-production-c568.up.railway.app/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
