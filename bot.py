import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes
from dotenv import load_dotenv
import asyncio

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
MAIN_MENU, BANK_SELECTION, CARD_TYPE_SELECTION, CARD_SELECTION, ALL_CARDS_VIEW = range(5)

# Данные о банках и картах
banks = {
    "Газпромбанк": {
        "Кредитные карты": {
            "Кредитная карта 180 дней": {
                "age_limit": 18,
                "advantages": [
                    "До 180 дней без процентов на покупки и снятие наличных",
                    "Кредитный лимит: до 600 000 рублей",
                    "Кэшбэк до 10% у партнеров банка",
                    "Процентная ставка от 11,9% годовых после льготного периода",
                    "Бесплатное обслуживание при тратах от 5 000 рублей в месяц, иначе — 199 рублей в месяц",
                    "Оформление онлайн и бесплатная доставка карты"
                ],
                "ref_link": "https://example.com/gazprombank_180"
            },
            "Кредитная карта 180 дней (для блогеров и соц. сетей)": {
                "age_limit": 18,
                "advantages": [
                    "До 180 дней без процентов на покупки и снятие наличных",
                    "Кредитный лимит: до 600 000 рублей",
                    "Повышенный кэшбэк для категорий, связанных с деятельностью в соцсетях и блогинге",
                    "Процентная ставка от 11,9% годовых после льготного периода",
                    "Бесплатное обслуживание при тратах от 5 000 рублей в месяц, иначе — 199 рублей в месяц",
                    "Специальные условия и бонусы для активных пользователей соцсетей"
                ],
                "ref_link": "https://example.com/gazprombank_bloggers"
            }
        },
        "Дебетовые карты": {
            "Премиум МИР Supreme": {
                "age_limit": 18,
                "advantages": [
                    "1,5% на все покупки",
                    "До 20% у партнеров банка",
                    "До 5% годовых на остаток средств",
                    "Бесплатное снятие наличных в банкоматах Газпромбанка",
                    "До 100 000 рублей в месяц без комиссии в банкоматах других банков",
                    "Бесплатные переводы через СБП до 100 000 рублей в месяц",
                    "Бесплатное пополнение с карт других банков",
                    "Бесплатное обслуживание при среднемесячном остатке от 100 000 рублей или тратах от 30 000 рублей в месяц, иначе — 199 рублей в месяц",
                    "Премиальная карта с выгодными условиями для активных пользователей"
                ],
                "ref_link": "https://example.com/gazprombank_premium_supreme"
            },
            "Дебетовая карта «Мир»": {
                "age_limit": 18,
                "advantages": [
                    "1% на все покупки",
                    "До 15% у партнеров банка",
                    "До 4% годовых на остаток средств",
                    "Бесплатное снятие наличных в банкоматах Газпромбанка",
                    "До 50 000 рублей в месяц без комиссии в банкоматах других банков",
                    "Бесплатные переводы через СБП до 100 000 рублей в месяц",
                    "Бесплатное пополнение с карт других банков",
                    "Бесплатное обслуживание при тратах от 5 000 рублей в месяц, иначе — 99 рублей в месяц",
                    "Оптимальный выбор для повседневных расходов с выгодным кэшбэком"
                ],
                "ref_link": "https://example.com/gazprombank_mir"
            }
        }
    },
    "Банк Зенит": {
        "Кредитные карты": {
            "Кредитная карта с кешбэком": {
                "age_limit": 18,
                "advantages": [
                    "Кэшбэк 1% на все покупки",
                    "5% в выбранных категориях",
                    "До 100 дней без процентов",
                    "Кредитный лимит: до 500 000 рублей",
                    "Процентная ставка от 12,5% годовых после льготного периода",
                    "Бесплатное обслуживание при тратах от 10 000 рублей в месяц, иначе — 149 рублей в месяц",
                    "Быстрое оформление и удобное мобильное приложение"
                ],
                "ref_link": "https://example.com/zenit_cashback"
            }
        }
    },
    "Т-Банк": {
        "Кредитные карты": {
            "Карта Платинум": {
                "age_limit": 18,
                "advantages": [
                    "Кэшбэк 1% на все покупки",
                    "До 30% у партнеров банка",
                    "До 55 дней без процентов",
                    "Кредитный лимит: до 700 000 рублей",
                    "Процентная ставка от 12% годовых после льготного периода",
                    "Бесплатное обслуживание при тратах от 3 000 рублей в месяц, иначе — 99 рублей в месяц",
                    "Оформление онлайн и бесплатная доставка карты"
                ],
                "ref_link": "https://example.com/tbank_platinum"
            },
            "Кредитная карта All Games": {
                "age_limit": 18,
                "advantages": [
                    "До 5% кэшбэка на покупки игр и внутриигровых товаров",
                    "До 55 дней без процентов",
                    "Кредитный лимит: до 700 000 рублей",
                    "Процентная ставка от 12% годовых после льготного периода",
                    "Бесплатное обслуживание при тратах от 3 000 рублей в месяц, иначе — 99 рублей в месяц",
                    "Специальные предложения для геймеров и бонусы в популярных играх"
                ],
                "ref_link": "https://example.com/tbank_allgames"
            }
        },
        "Дебетовые карты": {
            "Black": {
                "age_limit": 18,
                "advantages": [
                    "1% на все покупки",
                    "До 15% у партнеров банка",
                    "До 3% годовых на остаток свыше 10 000 рублей",
                    "Бесплатное снятие наличных в банкоматах Т-Банка",
                    "До 50 000 рублей в месяц без комиссии в банкоматах других банков",
                    "Бесплатные переводы через СБП до 100 000 рублей в месяц",
                    "Бесплатное пополнение с карт других банков",
                    "Бесплатное обслуживание при тратах от 5 000 рублей в месяц или среднемесячном остатке от 10 000 рублей, иначе — 149 рублей в месяц",
                    "Стильная карта с выгодными условиями для повседневного использования"
                ],
                "ref_link": "https://example.com/tbank_black"
            },
            "Premium": {
                "age_limit": 18,
                "advantages": [
                    "До 30% по спецпредложениям партнеров",
                    "До 15% за билеты в кино, театры, на концерты при покупке в Т‑Городе",
                    "До 10% за отели и авиабилеты в приложении Т‑Банка",
                    "До 5% за покупку продуктов Т‑Страхования",
                    "До 17% годовых по накопительному счету с подпиской Pro",
                    "Бесплатное снятие наличных от 3 000 до 100 000 рублей в любых банкоматах по всему миру",
                    "Бесплатное пополнение с карт других банков",
                    "Бесплатные переводы через СБП до 100 000 рублей в месяц",
                    "Бесплатное обслуживание при постоянном остатке на картсчетах, вкладах, накопительных счетах и в инвестициях от 50 000 рублей, иначе — 99 рублей в месяц",
                    "Премиальная карта с расширенными возможностями для взыскательных клиентов"
                ],
                "ref_link": "https://example.com/tbank_premium"
            }
        }
    },
        "СберБанк": {
        "Кредитные карты": {
            "Кредитная карта": {
                "age_limit": 18,
                "advantages": [
                    "До 50 дней без процентов",
                    "Кредитный лимит: до 600 000 рублей",
                    "Спасибо от Сбербанка: до 30% бонусами у партнеров",
                    "Процентная ставка от 11,9% годовых после льготного периода",
                    "От 0 до 750 рублей в год, в зависимости от типа карты",
                    "Широкая сеть обслуживания и бонусная программа"
                ],
                "ref_link": "https://example.com/sber_credit"
            }
        },
        "Дебетовые карты": {
            "СберКарта МИР": {
                "age_limit": 18,
                "advantages": [
                    "До 10% у партнеров",
                    "До 1,5% на все покупки",
                    "До 6% при остатке от 50 000 рублей",
                    "Бесплатное снятие наличных в банкоматах Сбербанка",
                    "Бесплатные переводы через СБП до 100 000 рублей",
                    "Бесплатное пополнение с карт других банков",
                    "Бесплатное обслуживание при тратах от 5 000 рублей в месяц, иначе — 150 рублей",
                    "Отличный выбор для клиентов Сбербанка с удобной бонусной программой"
                ],
                "ref_link": "https://example.com/sber_debit"
            }
        }
    },
    "Уралсиб Банк": {
        "Кредитные карты": {
            "Кредитная карта «120 дней»": {
                "age_limit": 18,
                "advantages": [
                    "До 120 дней без процентов на покупки и снятие наличных",
                    "Кредитный лимит: до 1 000 000 рублей",
                    "До 1,5% на все покупки",
                    "Процентная ставка от 13,9% годовых после льготного периода",
                    "Бесплатное обслуживание при тратах от 5 000 рублей в месяц, иначе — 199 рублей в месяц",
                    "Возможность бесплатного обслуживания и длительный льготный период"
                ],
                "ref_link": "https://example.com/uralsib_120"
            }
        },
        "Дебетовые карты": {
            "Прибыль": {
                "age_limit": 18,
                "advantages": [
                    "До 10% на любимые категории",
                    "1% на все покупки",
                    "До 6% годовых",
                    "Бесплатное снятие наличных в любых банкоматах при снятии от 3 000 рублей",
                    "Бесплатные переводы через СБП до 100 000 рублей",
                    "Бесплатное обслуживание при тратах от 10 000 рублей, иначе — 99 рублей",
                    "Оптимальная карта с высокой доходностью и хорошим кэшбэком"
                ],
                "ref_link": "https://example.com/uralsib_profit"
            }
        }
    },
    "Совкомбанк": {
        "Кредитные карты": {
            "Карта «Халва»": {
                "age_limit": 18,
                "advantages": [
                    "Беспроцентная рассрочка до 12 месяцев у партнеров банка",
                    "До 6% на остаток собственных средств",
                    "До 108 дней без процентов",
                    "Кредитный лимит: до 350 000 рублей",
                    "0% при покупках в рассрочку у партнеров",
                    "Бесплатное обслуживание"
                ],
                "ref_link": "https://example.com/sovcombank_halva"
            }
        }
    },
    "Ак Барс": {
        "Кредитные карты": {
            "Кредитная карта 115 дней": {
                "age_limit": 18,
                "advantages": [
                    "До 115 дней без процентов",
                    "Кредитный лимит: до 600 000 рублей"
                ],
                "ref_link": "https://example.com/akbars_115"
            }
        }
    },
    "АТБ": {
        "Кредитные карты": {
            "Кредитная карта «Универсальная»": {
                "age_limit": 18,
                "advantages": [
                    "Кэшбэк 1% на все покупки",
                    "До 10% у партнеров банка",
                    "До 50 дней без процентов",
                    "Кредитный лимит: до 500 000 рублей",
                    "Процентная ставка от 13,9% годовых после льготного периода",
                    "Бесплатное обслуживание при тратах от 5 000 рублей в месяц, иначе — 99 рублей",
                    "Универсальная карта с выгодным кэшбэком и длительным льготным периодом"
                ],
                "ref_link": "https://example.com/atb_universal"
            }
        }
    },
    "ВТБ": {
        "Кредитные карты": {
            "Кредитная карта": {
                "age_limit": 18,
                "advantages": [
                    "Кэшбэк 1,5% на все покупки",
                    "До 10% у партнеров банка",
                    "До 110 дней без процентов",
                    "Кредитный лимит: до 1 000 000 рублей",
                    "Процентная ставка от 14,6% годовых после льготного периода",
                    "Бесплатное обслуживание при тратах от 5 000 рублей в месяц, иначе — 249 рублей",
                    "Идеальный выбор для тех, кто ценит длительный льготный период и высокий кредитный лимит"
                ],
                "ref_link": "https://example.com/vtb_credit"
            }
        },
        "Дебетовые карты": {
            "МИР": {
                "age_limit": 18,
                "advantages": [
                    "1% на все покупки",
                    "До 10% у партнеров банка",
                    "До 5% годовых на остаток свыше 15 000 рублей",
                    "Бесплатное снятие наличных в банкоматах ВТБ",
                    "До 50 000 рублей в месяц без комиссии в банкоматах других банков",
                    "Бесплатные переводы через СБП до 100 000 рублей",
                    "Бесплатное пополнение с карт других банков",
                    "Бесплатное обслуживание при тратах от 5 000 рублей в месяц или среднемесячном остатке от 15 000 рублей, иначе — 249 рублей",
                    "Удобная карта с выгодными условиями для повседневных расходов"
                ],
                "ref_link": "https://example.com/vtb_mir"
            },
            "Платёжный стикер": {
                "age_limit": 18,
                "advantages": [
                    "1% на все покупки",
                    "До 10% у партнеров банка",
                    "До 5% годовых на остаток свыше 15 000 рублей",
                    "Бесплатное снятие наличных в банкоматах ВТБ",
                    "До 50 000 рублей в месяц без комиссии в банкоматах других банков",
                    "Бесплатные переводы через СБП до 100 000 рублей",
                    "Бесплатное пополнение с карт других банков",
                    "Бесплатное обслуживание при тратах от 5 000 рублей в месяц или среднемесячном остатке от 15 000 рублей, иначе — 249 рублей",
                    "Современное решение для бесконтактных платежей с выгодными условиями"
                ],
                "ref_link": "https://example.com/vtb_sticker"
            }
        }
    },
    "ОТП Банк": {
        "Дебетовые карты": {
            "Premium Light": {
                "age_limit": 18,
                "advantages": [
                    "1,5% на все покупки",
                    "До 20% у партнеров банка",
                    "До 4% годовых на остаток свыше 10 000 рублей",
                    "Бесплатное снятие наличных в банкоматах ОТП Банка",
                    "До 100 000 рублей в месяц без комиссии в банкоматах других банков",
                    "Бесплатные переводы через СБП до 100 000 рублей в месяц",
                    "Бесплатное пополнение с карт других банков",
                    "Бесплатное обслуживание при тратах от 10 000 рублей в месяц или среднемесячном остатке от 30 000 рублей, иначе — 199 рублей",
                    "Премиальная карта с привлекательными условиями для активных пользователей"
                ],
                "ref_link": "https://example.com/otp_premium_light"
            }
        }
    },
        "ФОРА-БАНК": {
        "Дебетовые карты": {
            "МИР «Все включено»": {
                "age_limit": 18,
                "advantages": [
                    "До 5% на покупки в категориях «Продукты», «Аптеки», «АЗС»",
                    "1% на все остальные покупки",
                    "До 6% годовых при остатке от 10 000 рублей",
                    "Бесплатное снятие наличных в любых банкоматах России от 3 000 рублей",
                    "Бесплатные переводы через СБП до 100 000 рублей",
                    "Бесплатное пополнение с карт других банков",
                    "Бесплатное обслуживание при ежемесячных тратах от 5 000 рублей, иначе — 99 рублей",
                    "Оптимальный вариант для тех, кто хочет получать высокий кэшбэк на повседневные покупки"
                ],
                "ref_link": "https://example.com/fora_all_inclusive"
            }
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

    return await show_card_type_selection(query)

# Новый обработчик выбора типа карты
async def show_card_type_selection(query) -> int:
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Кредитные карты", callback_data="credit_cards")],
        [InlineKeyboardButton("Дебетовые карты", callback_data="debit_cards")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_banks")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    await query.edit_message_text(
        "💳 <b>Выберите тип карты:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return CARD_TYPE_SELECTION

# Обработчик выбора типа карты
async def handle_card_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_banks":
        return await show_bank_selection(query)

    if query.data == "main_menu":
        return await return_to_main_menu(query)

    card_type = query.data
    context.user_data["card_type"] = "Кредитные карты" if card_type == "credit_cards" else "Дебетовые карты"

    return await show_card_selection(query, context.user_data["current_bank"])

# Обновляем показ списка карт выбранного банка в зависимости от типа карты
async def show_card_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    cards = banks[context.user_data["current_bank"]][context.user_data["card_type"]]
    filtered_cards = {k: v for k, v in cards.items()}

    keyboard = [
        [InlineKeyboardButton(card, callback_data=f"card_{card}")] for card in filtered_cards
    ] + [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_card_type")],
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

    if "current_bank" not in context.user_data or "card_type" not in context.user_data:
        return await return_to_main_menu(query)

    card_name = query.data.split("_", 1)[1]
    bank_name = context.user_data["current_bank"]
    card_info = banks[bank_name][context.user_data["card_type"]][card_name]

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
    for bank, types in banks.items():
        text += f"🏦 <b>{bank}</b>:\n"
        for card_type, cards in types.items():
            text += f"  <b>{card_type}:</b>\n"
            for card, info in cards.items():
                text += f"    • {card} ({info['age_limit']}+)\n"

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

    if query.data == "back_to_card_type":
        return await show_card_type_selection(query)

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

    async def startup_actions(app: Application):
        await app.bot.delete_webhook()
        logger.info("Webhook удален")

    async def shutdown_actions(app: Application):
        await app.shutdown()
        logger.info("Приложение остановлено")

    # Выполнение дополнительных действий при старте и завершении работы приложения
    application.initialize()
    asyncio.get_event_loop().run_until_complete(startup_actions(application))

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
            CARD_TYPE_SELECTION: [
                CallbackQueryHandler(handle_card_type_selection),
                CallbackQueryHandler(return_to_main_menu, pattern="^main_menu$")
            ],
            CARD_SELECTION: [
                CallbackQueryHandler(handle_card_selection),
                CallbackQueryHandler(handle_navigation, pattern="^main_menu$")
            ],
            ALL_CARDS_VIEW: [
                CallbackQueryHandler(handle_navigation, pattern="^main_menu$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
