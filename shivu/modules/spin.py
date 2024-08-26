import asyncio
import random
from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from telegram.error import BadRequest, RetryAfter

# Example imports, replace with actual database and collection references
from shivu import user_collection, collection, application

# Define rarity percentages
rarity_percentages = {
    "🔵 𝙇𝙊𝙒": 30,
    "🟢 𝙈𝙀𝘋𝙄𝙐𝙈": 30,
    "🔴 𝙃𝙄𝙂𝙃": 30,
    "🟡 𝙉𝙊𝘽𝙀𝙇": 10,
    "🥵 𝙉𝙐𝘿𝙀𝙎": 0,
    "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿": 0,
    "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]": 0,
    "⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚": 1,
    "🎭 𝙀𝙍𝙊𝙏𝙄𝘾": 0,
    "🍑 𝙎𝙪𝙡𝙩𝙧𝙮": 0
}

async def get_random_waifu(multiplier):
    try:
        all_characters = await collection.find().to_list(length=None)
        weighted_characters = [
            c for c in all_characters if 'rarity' in c
            for _ in range(int(multiplier * rarity_percentages.get(c['rarity'], 0)))
        ]
        if not weighted_characters:
            return None
        return random.choice(weighted_characters)
    except Exception as e:
        print(f"Error in get_random_waifu: {e}")
        return None

async def enter_spin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data = await user_collection.find_one({'id': user_id})
    
    if not user_data:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please start the bot first.")
        return
    
    now = datetime.utcnow()
    last_free_spin = user_data.get('last_free_spin')
    can_take_free_spin = not last_free_spin or (now - last_free_spin) > timedelta(days=1)
    keyboard_buttons = [
        [InlineKeyboardButton("1x Spin", callback_data="spin_1x"),
         InlineKeyboardButton("5x Spin", callback_data="spin_5x")]
    ]
    if can_take_free_spin:
        keyboard_buttons.insert(0, [InlineKeyboardButton("Free 1x Spin", callback_data="spin_free")])
    
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    image_url = "https://telegra.ph/file/7959c4cb32a33ceda8077.png"
    await update.message.reply_photo(photo=image_url, caption="Choose your spin option:\n\nFree 1x Spin = Once per day\n1x Spin = 1000 Tokens\n5x Spin = 4500 Tokens", reply_markup=keyboard)

async def spin_callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    
    # Check if user is authorized based on reply_to_message
    if query.message.reply_to_message is None or query.message.reply_to_message.from_user is None:
        await query.answer("You are not authorized to interact with this button.", show_alert=True)
        return
    
    user_id = query.from_user.id
    authorized_user_id = query.message.reply_to_message.from_user.id
    
    if user_id != authorized_user_id:
        await query.answer("You are not authorized to interact with this button.", show_alert=True)
        return
    
    # Proceed with spin logic
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await query.message.edit_caption("Please start the bot first.")
        return
    
    now = datetime.utcnow()
    if data == "spin_free":
        last_free_spin = user_data.get('last_free_spin')
        if last_free_spin and (now - last_free_spin) < timedelta(days=1):
            await query.message.edit_caption("You have already taken your free spin today. Try again tomorrow.")
            return
        
        await user_collection.update_one({'id': user_id}, {'$set': {'last_free_spin': now}})
        spin_type = "1x"
    else:
        spin_type = data.split("_")[1]
        balance = user_data.get('tokens', 0)
        spin_cost = 1000 if spin_type == "1x" else 4500
        if balance < spin_cost:
            await query.message.edit_caption("You don't have enough tokens to spin.")
            return
        
        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': -spin_cost}})
    
    multiplier = 100
    available_characters = []
    for _ in range(5 if spin_type == "5x" else 1):
        character = await get_random_waifu(multiplier)
        if character:
            available_characters.append(character)
    
    if not available_characters:
        await query.message.edit_caption("No waifus available.")
        return
    
    await user_collection.update_one(
        {'id': user_id},
        {'$push': {'characters': {'$each': available_characters}}}
    )
    
    keyboard_buttons = [
        [InlineKeyboardButton("1x Spin", callback_data="spin_1x"),
         InlineKeyboardButton("5x Spin", callback_data="spin_5x")]
    ]
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    
    try:
        await query.message.edit_caption("Spinning")
    except BadRequest as e:
        print(f"Failed to edit message: {e}")
        return

    # Simulate spinning process with moon phases
    moon_phases = ["🌑", "🌘", "🌗", "🌖", "🌕"]
    for phase in moon_phases:
        try:
            await query.message.edit_caption(f"Spinning {phase}")
            await asyncio.sleep(1) 
        except BadRequest as e:
            print(f"Failed to edit message: {e}")
            return
    
    # Prepare result text
    result_text = "\n".join([f"<b>{char['id']} | {char['name']} ( {char['rarity']} )</b>" for char in available_characters])
    
    # Edit final message with result
    try:
        await query.message.edit_caption(f"<b>You won the following characters:</b>\n<b>────────────────────</b>\n{result_text}\n<b>────────────────────</b>\n", reply_markup=keyboard, parse_mode='HTML')
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await query.message.edit_caption(f"<b>You won the following characters:</b>\n<b>────────────────────</b>\n{result_text}\n<b>────────────────────</b>\n", reply_markup=keyboard, parse_mode='HTML')
    except BadRequest as e:
        print(f"Failed to edit message: {e}")
        return

application.add_handler(CallbackQueryHandler(spin_callback_handler, pattern="^(spin_1x|spin_5x|spin_free)$", block=False))
application.add_handler(CommandHandler("spin", enter_spin))
