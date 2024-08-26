from pyrogram import Client, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import shivuu as bot
from telegram.ext import MessageHandler, filters
from shivu import user_collection, application

pending_gifts = {}

async def handle_gift_command(update: Update, context: CallbackContext):
    message = update.message
    sender_id = message.from_user.id

    if not message.reply_to_message:
        await message.reply_html("<b>You need to reply to a user's message to gift a slave!</b>")
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_username = message.reply_to_message.from_user.username
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply_html("<b>You can't gift a slave to yourself!</b>")
        return

    if len(message.text.split()) != 2:
        await message.reply_html("<b>You need to provide a slave ID!</b>")
        return

    character_id = message.text.split()[1]

    sender = await user_collection.find_one({'id': sender_id})

    character = next((character for character in sender.get('characters', []) if isinstance(character, dict) and character.get('id') == character_id), None)

    if not character:
        await message.reply_text("You don't have this slave in your collection!")
        return

    if sender_id in pending_gifts:
        await message.reply_html("<b>You already have a pending gift. Please confirm or cancel it before initiating a new one.</b>")
        return

    pending_gifts[sender_id] = {
        'character': character,
        'receiver_id': receiver_id,
        'receiver_username': receiver_username,
        'receiver_first_name': receiver_first_name
    }

    caption = (
        f"<b>Do you really want to gift this slave to {receiver_first_name}?</b>\n"
        f"<b>Name: {character['name']}</b>\n"
        f"<b>ID: {character['id']}</b>\n"
        f"<b>Rarity: {character['rarity']}</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("Confirm ✅", callback_data="confirm_gift")],
            [InlineKeyboardButton("Cancel ❌", callback_data="cancel_gift")]
        ]
    )

    await message.reply_text(caption, reply_markup=keyboard, parse_mode='HTML')

async def handle_callback_query(update: Update, context: CallbackContext):
    callback_query = update.callback_query
    sender_id = callback_query.from_user.id

    if sender_id not in pending_gifts:
        await callback_query.answer("No pending gift found.", show_alert=True)
        return

    gift = pending_gifts[sender_id]
    receiver_id = gift['receiver_id']

    if callback_query.data == "confirm_gift":
        sender = await user_collection.find_one({'id': sender_id})
        receiver = await user_collection.find_one({'id': receiver_id})

        sender['characters'].remove(gift['character'])
        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender['characters']}})

        if receiver:
            await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': gift['character']}})
        else:
            await user_collection.insert_one({
                'id': receiver_id,
                'username': gift['receiver_username'],
                'first_name': gift['receiver_first_name'],
                'characters': [gift['character']],
            })

        del pending_gifts[sender_id]

        await callback_query.message.edit_text(f"🎁 You have successfully gifted your slave to {gift['receiver_first_name']}!")

    elif callback_query.data == "cancel_gift":
        del pending_gifts[sender_id]
        await callback_query.message.edit_text("❌️ Gifting cancelled.")

# Registering handlers with the application
application.add_handler(CommandHandler("gift", handle_gift_command))
application.add_handler(CallbackQueryHandler(handle_callback_query, pattern='^confirm_gift$|^cancel_gift$', block=False))
