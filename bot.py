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
BOT_TOKEN = os.getenv("BOT_TOKEN", "8105012250:AAFmOW45SKDGrn0pqIFvSVhQv3uwodCMKXs")

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
    keyboard = []
    for row in buttons:
        keyboard.append([InlineKeyboardButton(btn[0], callback_data=btn[1])] if isinstance(row, tuple) else [InlineKeyboardButton(row, callback_data=row)])
    if back_button:
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=back_button)])
    return InlineKeyboardMarkup(keyboard)

# --- Основные обработчики ---
async def start(update: Update, context: CallbackContext):
    """Запуск бота с реферальной системой"""
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
        [InlineKeyboardButton("14-17 лет", callback_data="age_14_17")],
        [InlineKeyboardButton("18+ лет", callback_data="age_18_plus")]
    ]
    await update.message.reply_text(
        "👋 Привет! Я помогу тебе выбрать лучшую банковскую карту!\nВыбери свой возраст:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_AGE

async def handle_age(update: Update, context: CallbackContext):
    """Обработка выбора возраста"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user_data[user_id]['age'] = 14 if query.data == "age_14_17" else 18
    user_data[user_id]['points'] += 10  # Начисление баллов за начало работы
    
    await show_main_menu(query)
    return ConversationHandler.END

async def show_main_menu(query):
    """Обновлённое главное меню"""
    buttons = [
        ("🏦 Карты", "category_banks"),
        ("🔍 Сравнить", "compare_cards"),
        ("🎁 Акции", "promo"),
        ("🏆 Профиль", "profile")
    ]
    await query.edit_message_text(
        "🎮 Главное меню:",
        reply_markup=build_keyboard(buttons)
    )

async def profile(update: Update, context: CallbackContext):
    """Профиль пользователя с достижениями"""
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
        ("🔗 Пригласить друзей", "invite"),
        ("📈 Топ пользователей", "leaderboard"),
        ("🔙 Назад", "back_main")
    ]
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(buttons)
    )

async def invite(update: Update, context: CallbackContext):
    """Реферальная система"""
    query = update.callback_query
    user_id = query.from_user.id
    ref_link = f"https://t.me/{(await context.bot.get_me()).username}?start=ref_{user_id}"
    
    text = "🤝 Пригласи друзей и получай бонусы!\n\n"
    text += f"Ваша реферальная ссылка:\n{ref_link}\n\n"
    text += "За каждого приглашённого друга вы получаете:\n"
    text += "✅ 50 баллов\n✅ +1 к достижениям\n✅ Бонусные возможности"
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard([("🔙 Назад", "profile")])
    )

async def handle_card_selection(update: Update, context: CallbackContext):
    """Обновлённый обработчик выбора карт"""
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

# --- Доработанный вывод карт с кнопками ---
async def show_card_details(query, bank_name, card_name):
    """Обновлённый вывод карты с кнопками"""
    card = banks[bank_name][card_name]
    text = f"<b>{card_name}</b>\n\n"
    text += "📌 Основные преимущества:\n" + "\n".join(f"• {adv}" for adv in card['advantages'])
    
    buttons = [
        [InlineKeyboardButton("🖇️ Оформить карту", url=card['ref_link'])],
        [InlineKeyboardButton("⭐ Добавить в сравнение", callback_data=f"select_{bank_name}_{card_name}")]
    ]
    
    if 'promo' in card:
        buttons.append([InlineKeyboardButton("🎁 Акция", callback_data=f"promo_{bank_name}_{card_name}")])
    
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data=f"bank_{bank_name}")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )

# --- Новый обработчик акций ---
async def show_promo(update: Update, context: CallbackContext):
    """Улучшенный раздел акций"""
    query = update.callback_query
    text = "🎁 <b>Текущие акции:</b>\n\n"
    
    for bank, cards in banks.items():
        for card, data in cards.items():
            if 'promo' in data:
                text += f"🔥 <b>{card}</b>\n"
                text += "\n".join(f"• {p}" for p in data['promo']) + "\n\n"
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard([("🔙 Назад", "back_main")]),
        parse_mode="HTML"
    )

# --- Обновлённая система сравнения ---
async def compare_selected_cards(query):
    """Улучшенное сравнение карт"""
    user_id = query.from_user.id
    selected = user_data[user_id]['selected_cards']
    
    if not selected:
        await query.edit_message_text("❌ Выберите карты для сравнения!")
        return
    
    text = "🔍 <b>Сравнение карт:</b>\n\n"
    for card_name in selected:
        for bank, cards in banks.items():
            if card_name in cards:
                card = cards[card_name]
                text += f"▫️ <b>{card_name}</b>\n"
                text += f"Возраст: от {card['age_limit']}+ лет\n"
                text += "Преимущества:\n" + "\n".join(f"• {adv}" for adv in card['advantages']) + "\n\n"
    
    # Персональная рекомендация
    prefs = user_data[user_id]['preferences']
    if prefs:
        top_pref = max(prefs, key=prefs.get)
        text += f"\n🌟 Вам подходят карты с акцентом на <b>{top_pref}</b>!"
    
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard([("🔙 Назад", "compare_cards")]),
        parse_mode="HTML"
    )

def main():
    """Запуск бота с новыми обработчиками"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_AGE: [CallbackQueryHandler(handle_age)],
            SELECT_CARDS: [CallbackQueryHandler(handle_card_selection)]
        },
        fallbacks=[],
        per_message=False
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(profile, pattern="profile"))
    app.add_handler(CallbackQueryHandler(invite, pattern="invite"))
    app.add_handler(CallbackQueryHandler(show_promo, pattern="promo"))
    
    # Для Railway
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://web-production-c568.up.railway.app/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
