import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Информация о банках и картах
banks = {
    'Сбербанк': ['Карта 1', 'Карта 2'],
    'Альфа-Банк': ['Карта 3', 'Карта 4'],
}

cards_info = {
    'Карта 1': 'Срок получения: 7 дней\nВыгоды: Кэшбэк 5%\nТип: Дебетовая\nОформить: [ссылка]',
    'Карта 2': 'Срок получения: 5 дней\nВыгоды: Процент на остаток\nТип: Кредитная\nОформить: [ссылка]',
    'Карта 3': 'Срок получения: 10 дней\nВыгоды: Бесплатное обслуживание\nТип: Дебетовая\nОформить: [ссылка]',
    'Карта 4': 'Срок получения: 3 дня\nВыгоды: Премиальные услуги\nТип: Кредитная\nОформить: [ссылка]',
}

user_data = {}

# Обработчик команды /start
def start(update: Update, context: CallbackContext) -> None:
    user_data[update.message.chat_id] = {}
    keyboard = [[InlineKeyboardButton("Начать", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Привет! Сколько вам лет?', reply_markup=reply_markup)

# Обработчик нажатия кнопок
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    data = query.data

    if data == 'start':
        query.edit_message_text(text='Введите ваш возраст:')
        user_data[query.message.chat_id]['state'] = 'age'
    elif data.startswith('bank_'):
        bank = data.split('_')[1]
        user_data[query.message.chat_id]['bank'] = bank
        keyboard = []
        for card in banks[bank]:
            keyboard.append([InlineKeyboardButton(card, callback_data=f'card_{card}')])
        keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_banks')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=f'Карты в {bank}:', reply_markup=reply_markup)
    elif data.startswith('card_'):
        card = data.split('_')[1]
        bank = user_data[query.message.chat_id]['bank']
        info = cards_info.get(card, 'Информация о карте недоступна.')
        keyboard = [[InlineKeyboardButton("Оформить на лучших условиях", url="YOUR_REFERRAL_LINK")]]
        keyboard.append([InlineKeyboardButton("Назад", callback_data=f'back_to_bank_{bank}')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=info, reply_markup=reply_markup)
    elif data == 'back_to_banks':
        keyboard = []
        for bank in banks:
            keyboard.append([InlineKeyboardButton(bank, callback_data=f'bank_{bank}')])
        keyboard.append([InlineKeyboardButton("Все карты", callback_data='all_cards')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text='Выберите банк:', reply_markup=reply_markup)
    elif data.startswith('back_to_bank_'):
        bank = data.split('_')[2]
        keyboard = []
        for card in banks[bank]:
            keyboard.append([InlineKeyboardButton(card, callback_data=f'card_{card}')])
        keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_banks')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=f'Карты в {bank}:', reply_markup=reply_markup)

# Обработчик текстовых сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
    if user_data.get(update.message.chat_id, {}).get('state') == 'age':
        age = update.message.text
        try:
            age = int(age)
            user_data[update.message.chat_id]['age'] = age
            keyboard = []
            for bank in banks:
                keyboard.append([InlineKeyboardButton(bank, callback_data=f'bank_{bank}')])
            keyboard.append([InlineKeyboardButton("Все карты", callback_data='all_cards')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(f'Банки для вашего возраста {age}:', reply_markup=reply_markup)
        except ValueError:
            update.message.reply_text('Пожалуйста, введите корректный возраст.')

# Основная функция
def main() -> None:
    token = os.getenv("BOT_TOKEN")

    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Вебхуки для Railway
    PORT = int(os.environ.get('PORT', '8443'))
    APP_NAME = os.getenv("APP_NAME")  # Замените на ваше приложение на Railway

    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=token,
                          webhook_url=f"https://{APP_NAME}.railway.app/{token}")
    
    updater.idle()

if __name__ == '__main__':
    main()
