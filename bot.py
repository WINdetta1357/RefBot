from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
import logging
import os
from dotenv import load_dotenv
from collections import defaultdict

# --- Настройки ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s',
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
