from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext, ConversationHandler

# UR token
TOKEN = "Ur's bot token"

# ConversationHandler
NAME, ADDRESS, MENU_SELECTION, ORDER_CONFIRMATION, PAYMENT, FEEDBACK = range(6)

# Food Menu
MENU = {
    "Snacks": {
        "Salat": 5,
        "Wings BBQ": 6,
    },
    "Main dishes": {
        "Pizza": 10,
        "Burger": 7,
        "Sushi": 15
    },
    "Drinks": {
        "Coke": 2,
        "Lemonade Juice": 3
    }
}

def get_menu_keyboard(category=None):
    if category:
        items = MENU[category].keys()
        keyboard = [[InlineKeyboardButton(item, callback_data=item)] for item in items]
        keyboard.append([InlineKeyboardButton("Back", callback_data="back_to_categories")])
    else:
        categories = MENU.keys()
        keyboard = [[InlineKeyboardButton(category, callback_data=category)] for category in categories]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Welcome! You can order food here. Type /order to get started.')

async def order(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Please, send your name.')
    return NAME

async def name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text('Thanks! Now send your address.')
    return ADDRESS

async def address(update: Update, context: CallbackContext) -> int:
    context.user_data['address'] = update.message.text
    # Address validation
    if not any(char.isdigit() for char in context.user_data['address']):
        await update.message.reply_text('Please, enter a valid address.')
        return ADDRESS
    await update.message.reply_text('It\'s cool! Select a category:', reply_markup=get_menu_keyboard())
    return MENU_SELECTION

async def menu_selection(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    selected_item = query.data

    if selected_item == "back_to_categories":
        await query.edit_message_text('Select a category:', reply_markup=get_menu_keyboard())
        return MENU_SELECTION

    if selected_item in MENU:
        await query.edit_message_text(f"Select a dish from the category {selected_item}:", reply_markup=get_menu_keyboard(selected_item))
        return MENU_SELECTION

    for category in MENU.values():
        if selected_item in category:
            context.user_data['order'] = selected_item
            context.user_data['price'] = category[selected_item]
            await query.edit_message_text(f"You have chosen {selected_item}. Cost: ${category[selected_item]}. Do you confirm the order??")

            keyboard = [
                [InlineKeyboardButton("Confirm", callback_data='confirm')],
                [InlineKeyboardButton("Cancel", callback_data='cancel')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup)
            return ORDER_CONFIRMATION

async def order_confirmation(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == 'confirm':
        await query.edit_message_text("The order is confirmed. Choose your payment method:", reply_markup=get_payment_keyboard())
        return PAYMENT
    else:
        await query.edit_message_text("The order has been cancelled.")
        return ConversationHandler.END

def get_payment_keyboard():
    keyboard = [
        [InlineKeyboardButton("By a cash", callback_data='cash')],
        [InlineKeyboardButton("By a card", callback_data='card')],
    ]
    return InlineKeyboardMarkup(keyboard)

async def payment(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    payment_method = query.data
    context.user_data['payment_method'] = payment_method
    await query.edit_message_text(f"Thank you for your order, {context.user_data['name']}! We will deliver it to the address {context.user_data['address']} As soon as possible. Payment: {payment_method}.")
    await update.effective_message.reply_text("Please leave your feedback about the order.")
    return FEEDBACK

async def feedback(update: Update, context: CallbackContext) -> int:
    context.user_data['feedback'] = update.message.text
    await update.message.reply_text("Thank you for your feedback!")
    # Save the order to history list
    user_data = context.user_data
    order_history = context.bot_data.setdefault("order_history", [])
    order_history.append(user_data)
    return ConversationHandler.END

async def view_order_history(update: Update, context: CallbackContext) -> None:
    order_history = context.bot_data.get("order_history", [])
    if not order_history:
        await update.message.reply_text("You have no previous orders.")
        return

    message = "Order History:\n"
    for order in order_history:
        message += f"\nName: {order['name']}, Address: {order['address']}, Order: {order['order']}, Cost: ${order['price']}, Payment: {order['payment_method']}, Feedback: {order['feedback']}\n"

    await update.message.reply_text(message)

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('order', order)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, address)],
            MENU_SELECTION: [CallbackQueryHandler(menu_selection)],
            ORDER_CONFIRMATION: [CallbackQueryHandler(order_confirmation)],
            PAYMENT: [CallbackQueryHandler(payment)],
            FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback)],
        },
        fallbacks=[]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("history", view_order_history))

    application.run_polling()

if __name__ == '__main__':
    main()
