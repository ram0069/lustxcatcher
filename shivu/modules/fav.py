from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import user_collection, collection
from shivu import application
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from telegram.error import BadRequest
async def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_html("<b>Please provide SLAVE ID...</b>")
        return
    character_id = context.args[0]
    
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await update.message.reply_html("<b>You do not have any SLAVE yet...</b>")
        return
    character = next((c for c in user['characters'] if isinstance(c, dict) and c.get('id') == character_id), None)
    if not character:
        await update.message.reply_html("<b>This SLAVE is Not In your SLAVE list</b>")
        return
    
    # Prepare confirmation message with inline keyboard
    confirmation_text = f"<b>Do you want to Marry {character['name']} As Your Slave?</b>"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Yes ✅", callback_data=f"fav_yes_{user_id}_{character_id}"),
         InlineKeyboardButton("No ❌", callback_data=f"fav_no_{user_id}_{character_id}")]
    ])

    # Send confirmation message
    await update.message.reply_photo(photo=character['img_url'], caption=confirmation_text, reply_markup=keyboard, parse_mode='HTML')

async def confirm_fav_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split('_')
    
    if data[0] == 'fav':
        callback_user_id = int(data[2])
        character_id = data[3]
        
        if user_id != callback_user_id:
            await query.answer("You are not authorized to use this button.", show_alert=True)
            return
        
        user = await user_collection.find_one({'id': user_id})
        if not user:
            await query.edit_message_caption(caption="<b>You do not have any SLAVE yet...</b>", parse_mode='HTML')
            return
        character = next((c for c in user['characters'] if isinstance(c, dict) and c.get('id') == character_id), None)
        if not character:
            await query.edit_message_caption(caption="<b>This SLAVE is Not In your SLAVE list</b>", parse_mode='HTML')
            return
        
        if data[1] == 'yes':
            user['favorites'] = [character_id]
            await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})
            await query.edit_message_caption(caption=f"<b>{character['name']} has been married as your Slave!</b>", parse_mode='HTML')
        elif data[1] == 'no':
            await query.edit_message_caption(caption="<b>Marry action has been cancelled.</b>", parse_mode='HTML')
application.add_handler(CommandHandler("marry", fav, block=False))
application.add_handler(CallbackQueryHandler(confirm_fav_callback, pattern='fav_yes|fav_no', block=False))
