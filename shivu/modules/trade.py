from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import shivuu as bot
from shivu import user_collection, application
import asyncio

pending_trades = {}

def mention_html(user_id, name):
    return f'<a href="tg://user?id={user_id}">{name}</a>'

async def handle_trade_command(update: Update, context: CallbackContext):
    message = update.message
    sender_id = message.from_user.id

    if not message.reply_to_message:
        await message.reply_html("<b>You need to reply to a user's message to trade a slave!</b>")
        return

    receiver_id = message.reply_to_message.from_user.id
    if sender_id == receiver_id:
        await message.reply_html("<b>You can't trade a slave with yourself!</b>")
        return

    if len(context.args) != 2:
        await message.reply_html("<b>You need to provide two slave IDs!</b>")
        return

    sender_character_id, receiver_character_id = context.args[0], context.args[1]

    sender = await user_collection.find_one({'id': sender_id})
    receiver = await user_collection.find_one({'id': receiver_id})

    # Ensure 'characters' is a list
    if not isinstance(sender.get('characters'), list):
        await message.reply_html("<b>Your characters data is corrupted!</b>")
        return
    if not isinstance(receiver.get('characters'), list):
        await message.reply_html("<b>The other user's characters data is corrupted!</b>")
        return

    sender_character = next((character for character in sender['characters'] if character['id'] == sender_character_id), None)
    receiver_character = next((character for character in receiver['characters'] if character['id'] == receiver_character_id), None)

    if not sender_character:
        await message.reply_text("<b>You don't have the slave you're trying to trade!</b>")
        return
    if not receiver_character:
        await message.reply_text("<b>The other user doesn't have the slave they're trying to trade!</b>")
        return

    if (sender_id, receiver_id) in pending_trades:
        await message.reply_text("<b>There is already a pending trade between you and this user.</b>")
        return

    pending_trades[(sender_id, receiver_id)] = {
        'sender_character_id': sender_character_id,
        'receiver_character_id': receiver_character_id
    }

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Confirm ✅", callback_data="confirm_trade")],
            [InlineKeyboardButton("Cancel ❌", callback_data="cancel_trade")]
        ]
    )

    mention = mention_html(message.reply_to_message.from_user.id, message.reply_to_message.from_user.first_name)
    await message.reply_html(f"{mention}, do you accept this trade?", reply_markup=keyboard)

async def on_callback_query(update: Update, context: CallbackContext):
    callback_query = update.callback_query
    receiver_id = callback_query.from_user.id

    for (sender_id, _receiver_id), trade_data in pending_trades.items():
        if _receiver_id == receiver_id:
            break
    else:
        await callback_query.answer("This is not for you!", show_alert=True)
        return

    if callback_query.data == "confirm_trade":
        sender = await user_collection.find_one({'id': sender_id})
        receiver = await user_collection.find_one({'id': receiver_id})

        sender_character_id = trade_data['sender_character_id']
        receiver_character_id = trade_data['receiver_character_id']

        # Ensure 'characters' is a list
        if not isinstance(sender.get('characters'), list) or not isinstance(receiver.get('characters'), list):
            await callback_query.message.edit_text("One of the users' characters data is corrupted!")
            del pending_trades[(sender_id, receiver_id)]
            return

        sender_character = next((character for character in sender['characters'] if character['id'] == sender_character_id), None)
        receiver_character = next((character for character in receiver['characters'] if character['id'] == receiver_character_id), None)

        if not sender_character or not receiver_character:
            await callback_query.message.edit_text("One of the characters in the trade no longer exists!")
            del pending_trades[(sender_id, receiver_id)]
            return

        sender['characters'].remove(sender_character)
        receiver['characters'].remove(receiver_character)

        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender['characters']}})
        await user_collection.update_one({'id': receiver_id}, {'$set': {'characters': receiver['characters']}})

        sender['characters'].append(receiver_character)
        receiver['characters'].append(sender_character)

        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender['characters']}})
        await user_collection.update_one({'id': receiver_id}, {'$set': {'characters': receiver['characters']}})

        del pending_trades[(sender_id, receiver_id)]

        mention = mention_html(callback_query.message.reply_to_message.from_user.id, callback_query.message.reply_to_message.from_user.first_name)
        await callback_query.message.edit_text(f"🎁 You have successfully traded your slave!")

    elif callback_query.data == "cancel_trade":
        del pending_trades[(sender_id, receiver_id)]
        await callback_query.message.edit_text("❌️ Trade canceled.")

application.add_handler(CommandHandler("trade", handle_trade_command, block=False))
application.add_handler(CallbackQueryHandler(on_callback_query, pattern='^confirm_trade$|^cancel_trade$', block=False))
