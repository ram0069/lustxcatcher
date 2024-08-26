from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from pyrogram.types import CallbackQuery
import asyncio
import random
from telegram import Update
from datetime import datetime, timedelta
from telegram.ext import CallbackContext
from pyrogram import Client, filters
from shivu import user_collection, collection, application

# User ID of the authorized user who can reset passes
AUTHORIZED_USER_ID = 7011990425

async def get_random_character():
    target_rarities = ['🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿', '🟡 𝙉𝙊𝘽𝙀𝙇']  # Example rarities
    selected_rarity = random.choice(target_rarities)
    try:
        pipeline = [
            {'$match': {'rarity': selected_rarity}},
            {'$sample': {'size': 1}}  # Adjust Num
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(e)
        return []

async def get_user_data(user_id):
    user = await user_collection.find_one({'id': user_id})
    if not user:
        user = {
            'id': user_id,
            'balance': 0,
            'tokens': 0,
            'pass': False,
            'pass_expiry': None,
            'daily_claims': 0,
            'weekly_claims': 0,
            'bonus_claimed': False,
            'last_claim_date': None,
            'last_weekly_claim_date': None,
            'pass_details': {
                'total_claims': 0,
                'daily_claimed': False,
                'weekly_claimed': False,
                'last_weekly_claim_date': None
            }
        }
        await user_collection.insert_one(user)
    return user

async def pass_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = await get_user_data(user_id)
    
    if not user_data.get('pass'):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Buy Pass (30000 tokens)", callback_data=f'buy_pass:{user_id}')]
        ])
        await update.message.reply_html("<b>You don't have a membership pass. buy one to unlock extra rewards.</b>", reply_markup=keyboard)
        return
    
    pass_details = user_data.get('pass_details', {})
    pass_expiry_date = datetime.now() + timedelta(days=7)
    pass_details['pass_expiry'] = pass_expiry_date
    user_data['pass_details'] = pass_details
    
    total_claims = pass_details.get('total_claims', 0)
    pass_details['total_claims'] = total_claims
    
    await user_collection.update_one({'id': user_id}, {'$set': user_data})
    
    pass_expiry = pass_expiry_date.strftime("%m-%d")
    daily_claimed = "✅" if pass_details.get('daily_claimed', False) else "❌"
    weekly_claimed = "✅" if pass_details.get('weekly_claimed', False) else "❌"
    
    pass_info_text = (
        f"❰ 𝗦 𝗟 𝗔 𝗩 𝗘 𝗣 𝗔 𝗦 𝗦 🎟️ ❱\n"
        f"▰▱▰▱▰▱▰▱▰▱\n\n"
        f"● Owner of pass : {update.effective_user.first_name}\n"
        f"───────────────\n"
        f"● Daily Claimed: {daily_claimed}\n"
        f"● Weekly Claimed: {weekly_claimed}\n"
        f"● Total Claims: {total_claims}\n"
        f"───────────────\n"
        f"● Pass Expiry: Sunday"
    )
    
    await update.message.reply_text(pass_info_text)

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query_data = query.data.split(':')
    action = query_data[0]
    user_id = int(query_data[1])
    
    if query.from_user.id != user_id:
        await query.answer("You are not authorized to use this button.", show_alert=True)
        return
    
    if action == 'buy_pass':
        user_data = await get_user_data(user_id)
        if user_data.get('pass'):
            await query.answer("You already have a membership pass.", show_alert=True)
            return
        
        if user_data['tokens'] < 30000:
            await query.answer("You don't have enough tokens to buy a pass.", show_alert=True)
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Confirm ✅", callback_data=f'confirm_buy_pass:{user_id}')],
            [InlineKeyboardButton("Cancel ❌", callback_data=f'cancel_buy_pass:{user_id}')],
        ])
        await query.message.edit_text("Are you sure you want to buy a pass for 30000 tokens?", reply_markup=keyboard)
    
    elif action == 'claim_free_pass':
        user_data = await get_user_data(user_id)
        if user_data.get('pass'):
            await query.answer("You already have a membership pass.", show_alert=True)
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Confirm ✅", callback_data=f'confirm_claim_free_pass:{user_id}')],
            [InlineKeyboardButton("Cancel ❌", callback_data=f'cancel_claim_free_pass:{user_id}')],
        ])
        await query.message.edit_text("Are you sure you want to claim a free pass?", reply_markup=keyboard)

async def confirm_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query_data = query.data.split(':')
    action = query_data[0]
    user_id = int(query_data[1])
    
    if query.from_user.id != user_id:
        await query.answer("You are not authorized to use this button.", show_alert=True)
        return
    
    if action == 'confirm_buy_pass':
        user_data = await get_user_data(user_id)
        if user_data.get('pass'):
            await query.answer("You already have a membership pass.", show_alert=True)
            return
        
        user_data['tokens'] -= 30000
        user_data['pass'] = True
        await user_collection.update_one({'id': user_id}, {'$set': {'tokens': user_data['tokens'], 'pass': True}})
        
        await query.message.edit_text("Pass successfully purchased. Enjoy your new benefits!")
    
    elif action == 'cancel_buy_pass':
        await query.message.edit_text("Purchase canceled.")
    
    elif action == 'confirm_claim_free_pass':
        user_data = await get_user_data(user_id)
        if user_data.get('pass'):
            await query.answer("You already have a membership pass.", show_alert=True)
            return
        
        user_data['pass'] = True
        pass_details = {
            'pass_expiry': datetime.now() + timedelta(days=7),
            'total_claims': 0,
            'daily_claimed': False,
            'weekly_claimed': False
        }
        user_data['pass_details'] = pass_details
        
        await user_collection.update_one({'id': user_id}, {'$set': user_data})
        
        await query.message.edit_text("Free pass successfully claimed. Enjoy your new benefits!")
    
    elif action == 'cancel_claim_free_pass':
        await query.message.edit_text("Claim canceled.")

async def claim_daily_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_data = await get_user_data(user_id)
    
    if not user_data.get('pass'):
        await update.message.reply_html(f"<b>{user_name}, you don't have a membership pass. Buy one to unlock extra rewards.\nDo /pass to buy.</b>")
        return
    
    pass_details = user_data.get('pass_details', {})
    last_claim_date = pass_details.get('last_claim_date')
    
    if last_claim_date:
        time_since_last_claim = datetime.now() - last_claim_date
        if time_since_last_claim < timedelta(hours=24):
            await update.message.reply_html(f"<b>{user_name}, you can only claim daily rewards once every 24 hours.</b>")
            return

    # Get the current day of the week
    today = datetime.now().weekday()

    # Set rewards for each day
    daily_rewards = {
        0: 1000,  # Monday
        1: 500, # Tuesday
        2: 1500,  # Wednesday
        3: 5000,  # Thursday
        4: 1500, # Friday
        5: 3000, # Saturday
        6: 5000  # Sunday
    }

    daily_reward = daily_rewards.get(today, 500)  # Default to 500 if day not found

    characters = await get_random_character()
    if not characters:
        await update.message.reply_html(f"<b>{user_name}, failed to fetch a random character for your daily reward.</b>")
        return

    character = characters[0]
    character_info_text = (
        f"<b>{character['name']}</b> from <i>{character['anime']}</i> : \n"
        f"{character['rarity']}\n"
    )
    
    pass_details['last_claim_date'] = datetime.now()
    pass_details['daily_claimed'] = True
    pass_details['total_claims'] = pass_details.get('total_claims', 0) + 1
    
    await user_collection.update_one(
        {'id': user_id},
        {
            '$inc': {'tokens': daily_reward},
            '$set': {'pass_details': pass_details},
            '$push': {'characters': character}
        }
    )
    
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=character['img_url'],
        caption=f"❰ <b>𝗣 𝗔 𝗦 𝗦 𝗗 𝗔 𝗜 𝗟 𝗬 🎁</b> ❱\n\n{character_info_text}\nReward: <b>{daily_reward} Tokens</b>.",
        parse_mode='HTML',
        reply_to_message_id=update.message.message_id
    )
    
async def claim_weekly_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = await get_user_data(user_id)
    
    if not user_data.get('pass'):
        await update.message.reply_html("<b>You don't have a membership pass. Buy one to unlock extra rewards.\nDo /pass to buy.</b>")
        return
    
    pass_details = user_data.get('pass_details', {})
    if pass_details.get('total_claims', 0) < 6:
        await update.message.reply_html("<b>You must claim daily rewards 6 times to claim the weekly reward.</b>")
        return

    today = datetime.utcnow()
    last_weekly_claim_date = pass_details.get('last_weekly_claim_date')
    if last_weekly_claim_date and (today - last_weekly_claim_date).days <= 7:
        await update.message.reply_html("<b>You have already claimed your weekly reward.</b>")
        return

    weekly_reward = 5000
    pass_details['weekly_claimed'] = True
    pass_details['last_weekly_claim_date'] = today
    pass_details['total_claims'] = pass_details.get('total_claims', 0) + 1
    
    await user_collection.update_one(
        {'id': user_id},
        {
            '$inc': {'tokens': weekly_reward},
            '$set': {'pass_details': pass_details}
        }
    )
    
    await update.message.reply_html("<b>❰ 𝗣 𝗔 𝗦 𝗦 𝗪 𝗘 𝗘 𝗞 𝗟 𝗬 🎁 ❱\n\n10000 tokens claimed.</b>")

async def claim_pass_bonus_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = await get_user_data(user_id)
    # Check if the user has a pass
    if not user_data.get('pass'):
        await update.message.reply_html("<b>You don't have a membership pass. Buy one to unlock extra rewards.\nDo /pass to buy.</b>")
        return
    # Get the user's current streak
    current_streak = user_data.get('streak', 0)


    if current_streak < 10:
        await update.message.reply_html(f"<b>You need to maintain a streak of 10 in /guess to claim the pass bonus.\nYour current streak : {current_streak}⚡️.</b>")
        return

    PASS_BONUS_TOKENS = 500  
    await user_collection.update_one({'id': user_id}, {
        '$inc': {'tokens': PASS_BONUS_TOKENS},
        '$set': {'streak': 0}
    })

    await update.message.reply_html("<b>❰ 𝗣 𝗔 𝗦 𝗦  𝗕 𝗢 𝗡 𝗨 𝗦 🎁 ❱\n500 tokens! Your streak has been reset.</b>")

async def reset_passes_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    # Check if the user issuing the command is the authorized user
    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_html("<b>You are not authorized to reset passes.</b>")
        return

    # Reset the pass status for all users
    await user_collection.update_many(
        {},
        {
            '$set': {
                'pass': False,
                'pass_details': {
                    'total_claims': 0,
                    'daily_claimed': False,
                    'weekly_claimed': False,
                    'last_weekly_claim_date': None,
                    'pass_expiry': None
                }
            }
        }
    )
    
    await update.message.reply_html("<b>All passes have been reset. Users will need to buy again.</b>")

# Register the command handler
application.add_handler(CommandHandler("pbonus", claim_pass_bonus_cmd))
application.add_handler(CommandHandler("pass", pass_cmd, block=False))
application.add_handler(CommandHandler("claim", claim_daily_cmd, block=False))
application.add_handler(CommandHandler("sweekly", claim_weekly_cmd, block=False))
application.add_handler(CommandHandler("rpass", reset_passes_cmd, block=False))
application.add_handler(CallbackQueryHandler(button_callback, pattern='buy_pass:.*|claim_free_pass:.*', block=False))
application.add_handler(CallbackQueryHandler(confirm_callback, pattern='confirm_buy_pass:.*|cancel_buy_pass:.*|confirm_claim_free_pass:.*|cancel_claim_free_pass:.*', block=False))
