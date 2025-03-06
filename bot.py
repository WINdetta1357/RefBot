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

    if selected_bank not in banks:
        await query.edit_message_text("Выбранный банк не найден.")
        return SELECT_BANK

    keyboard = []
    for card_name, data in banks[selected_bank].items():
        if user_data[user_id]['age'] >= data.get('age_limit', 0):
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

    if card_name not in banks[selected_bank]:
        await query.edit_message_text("Выбранная карта не найдена.")
        return SELECT_CARDS

    card = banks[selected_bank][card_name]
    text = f"🏦 <b>{selected_bank}</b> - <b>{card_name}</b>\n\n"
    text += "🔥 <u>Преимущества:</u>\n- " + "\n- ".join(card["advantages"]) + "\n\n"
    text += f"📋 <u>Условия получения:</u>\n- " + "\n- ".join(card.get("requirements", ["Нет требований"])) + "\n"

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
            text += f"📋 <u>Условия получения:</u>\n- " + "\n- ".join(card.get("requirements", ["Нет требований"])) + "\n"
            text += f"🔗 <a href='{card['ref_link']}'>Ссылка на карту</a>\n\n"

    keyboard = [("🔙 Назад", "back_bank")]
    await query.edit_message_text(
        text,
        reply_markup=build_keyboard(keyboard),
        parse_mode="HTML"
    )
    return SELECT_BANK

