reply_markup=build_keyboard(keyboard)
    )

async def handle_bank_selection(update: Update, context: CallbackContext):
    """Обработка выбора банка"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data.startswith("select_bank_"):
        bank_name = query.data.split("_", 2)[2]
        user_data[user_id]['selected_bank'] = bank_name

        # Переход в меню выбора карт
        await show_card_selection(query)
        return SELECT_CARDS

    elif query.data == "compare_all_cards":
        await compare_all_cards(query)
        return COMPARE_CARDS

    elif query.data == "change_age":
        await start(update, context)
        return ASK_AGE

async def show_card_selection(query):
    """Меню выбора карт"""
    user_id = query.from_user.id
    selected_bank = user_data[user_id]['selected_bank']

    keyboard = []
    for card_name, data in banks[selected_bank].items():
        if user_data[user_id]['age'] >= data['age_limit']:
            text = card_name
            keyboard.append((text, f"show_card_{card_name}"))

    keyboard.append(("🔙 Назад", "back_bank"))

    await query.edit_message_text(
        f"🔍 Выбери карту в банке {selected_bank}:",
        reply_markup=build_keyboard(keyboard)
    )

async def handle_card_info(update: Update, context: CallbackContext):
    """Показать информацию о карте и кнопку для оформления"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    selected_bank = user_data[user_id]['selected_bank']
    card_name = query.data.split("_", 2)[2]
    card = banks[selected_bank][card_name]

    text = f"🏦 <b>{selected_bank}</b> - <b>{card_name}</b>\n\n"
    text += "🔥 <u>Преимущества:</u>\n- " + "\n- ".join(card["advantages"]) + "\n\n"
    text += f"🚀 <u>Скорость выпуска:</u> {card['release_time']}\n\n"
    text += f"📋 <u>Условия получения:</u>\n- " + "\n- ".join(card["requirements"]) + "\n"

    keyboard = [
        [InlineKeyboardButton("Оформить на лучших условиях", url=card['ref_link'])],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_cards")]
    ]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SELECT_CARDS
async def compare_all_cards(update: Update, context: CallbackContext):
    """Сравнение всех карт"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    text = "🔍 <b>Сравнение всех карт:</b>\n\n"

    for bank_name, cards in banks.items():
        for card_name, card in cards.items():
            text += f"🏦 <b>{bank_name}</b> - <b>{card_name}</b>\n"
            text += "🔥 <u>Преимущества:</u>\n- " + "\n- ".join(card["advantages"]) + "\n"
            text += f"🚀 <u>Скорость выпуска:</у> {card['release_time']}\n"
            text += f"📋 <u>Условия получения:</u>\n- " + "\н- ".join(card["requirements"]) + "\n"
            text += f"🔗 <a href='{card['ref_link']}'>Ссылка на карту</a>\n\n"

    keyboard = [("🔙 Назад", "back_bank")]
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
    return SELECT_BANK

async def handle_back_cards(update: Update, context: CallbackContext):
    """Обработка кнопки 'Назад'"""
    query = update.callback_query
    await query.answer()
    await show_card_selection(query)
    return SELECT_CARDS

async def handle_back_bank(update: Update, context: CallbackContext):
    """Обработка кнопки 'Назад' в меню выбора банка"""
    query = update.callback_query
    await query.answer()
    await show_bank_selection(query)
    return SELECT_BANK

# --- Запуск бота ---

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_AGE: [CallbackQueryHandler(handle_age)],SELECT_BANK: [CallbackQueryHandler(handle_bank_selection), CallbackQueryHandler(handle_back_bank, pattern="^back_bank$")],
            SELECT_CARDS: [CallbackQueryHandler(handle_card_info, pattern="^show_card_"), CallbackQueryHandler(handle_back_cards, pattern="^back_bank$")],
            COMPARE_CARDS: [CallbackQueryHandler(compare_all_cards, pattern="^compare_all_cards$")]
        },
        fallbacks=[],
        per_user=True,
        per_chat=True,
        per_message=False
    )

    app.add_handler(conv_handler)

    app.run_polling()

if name == "__main__":
    main()
