from pyrogram import Client, filters
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from pyrogram.types import CallbackQuery
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from pymongo import MongoClient
from telegram.error import RetryAfter
from datetime import datetime, timedelta
import random
import time
import logging
import traceback
from collections import defaultdict
import asyncio
from shivu import user_collection, collection, application, safari_cooldown_collection, safari_users_collection
from shivu import shivuu as app


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


sessions = {}
safari_users = {}
allowed_group_id = -1002041586214
current_hunts = {}
current_engagements = {}
  
async def get_random_waifu():
    target_rarities = ['🟡 𝙉𝙊𝘽𝙀𝙇', '🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿']  # Example rarities
    selected_rarity = random.choice(target_rarities)
    try:
        pipeline = [
            {'$match': {'rarity': selected_rarity}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        if characters:
            waifu = characters[0]
            waifu_id = waifu['id']
            # Add waifu to sessions
            sessions[waifu_id] = waifu
            return waifu
        else:
            return None
    except Exception as e:
        print(e)
        return None

async def load_safari_users():
    async for user_data in safari_users_collection.find():
        safari_users[user_data['user_id']] = {
            'safari_balls': user_data['safari_balls'],
            'hunt_limit': user_data['hunt_limit'],
            'used_hunts': user_data['used_hunts']
        }

async def save_safari_user(user_id):
    user_data = safari_users[user_id]
    await safari_users_collection.update_one(
        {'user_id': user_id},
        {'$set': user_data},
        upsert=True
    )

async def safe_send_message(bot, chat_id, text):
    retry_after = 0
    while True:
        try:
            return await bot.send_message(chat_id=chat_id, text=text)
        except RetryAfter as e:
            retry_after = e.retry_after
            logger.warning(f"Flood control exceeded. Retrying in {retry_after} seconds.")
            await asyncio.sleep(retry_after)

async def enter_safari(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    if user_id in safari_users:
        await safe_send_message(context.bot, message.chat_id, "You are already in the slave zone!")
        return

    current_time = time.time()

    cooldown_doc = await safari_cooldown_collection.find_one({'user_id': user_id})

    if cooldown_doc:
        last_entry_time = cooldown_doc['last_entry_time']
    else:
        last_entry_time = 0

    cooldown_duration = 5 * 60 * 60  # 5 hours in seconds

    if current_time - last_entry_time < cooldown_duration:
        remaining_time = int(cooldown_duration - (current_time - last_entry_time))
        await safe_send_message(context.bot, message.chat_id, f"You can enter the slave zone again in {remaining_time // 3600} hours and {(remaining_time % 3600) // 60} minutes.")
        return

    user_data = await user_collection.find_one({'id': user_id})
    if user_data is None:
        await safe_send_message(context.bot, message.chat_id, "You need to register first by starting the bot in dm.")
        return

    entry_fee = 10000
    if user_data.get('tokens', 0) < entry_fee:
        await safe_send_message(context.bot, message.chat_id, "You don't have enough tokens to enter the slave zone.\nNeed 10,000 tokens.")
        return

    new_tokens = user_data['tokens'] - entry_fee
    await user_collection.update_one({'id': user_id}, {'$set': {'tokens': new_tokens}})

    await safari_cooldown_collection.update_one(
        {'user_id': user_id},
        {'$set': {'last_entry_time': current_time}},
        upsert=True
    )

    safari_users[user_id] = {
        'safari_balls': 30,
        'hunt_limit': 30,
        'used_hunts': 0
    }

    await save_safari_user(user_id)

    await safe_send_message(context.bot, message.chat_id, f"<b>Welcome to the slave Zone!\nEntry fee deducted: {entry_fee} Tokens\n\nBegin your /explore for rare slave.</b>")

async def exit_safari(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    if user_id not in safari_users:
        await message.reply_text("You are not in the slave zone!")
        return

    del safari_users[user_id]
    await safari_users_collection.delete_one({'user_id': user_id})

    await message.reply_text("You have now exited the slave Zone")

user_locks = defaultdict(asyncio.Lock)

async def hunt(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    async with user_locks[user_id]:
        if user_id not in safari_users:
            await message.reply_text("Not in the slave zone. use /stour first")
            return

        if user_id in current_hunts and current_hunts[user_id] is not None:
            if user_id not in current_engagements:
                await message.reply_text("You already have an ongoing hunt. Finish it first!")
                return

        user_data = safari_users[user_id]
        if user_data['used_hunts'] >= user_data['hunt_limit']:
            await message.reply_text("You have reached your hunt limit.")
            del safari_users[user_id]
            await safari_users_collection.delete_one({'user_id': user_id})
            return

        if user_data['safari_balls'] <= 0:
            await message.reply_text("You have run out of contract crystals.")
            del safari_users[user_id]
            await safari_users_collection.delete_one({'user_id': user_id})
            return

        waifu = await get_random_waifu()
        if not waifu:
            await message.reply_text("No slave available.")
            return

        waifu_name = waifu['name']
        waifu_img_url = waifu['img_url']
        waifu_id = waifu['id']
        waifu_rarity = waifu['rarity']

        if user_id in current_hunts:
            del current_hunts[user_id]

        current_hunts[user_id] = waifu_id

        user_data['used_hunts'] += 1
        safari_users[user_id] = user_data

        await save_safari_user(user_id)

        text = f"<b>A wild {waifu_name} ( {waifu_rarity} ) has appeared!</b>\n\n<b>/explore limit: {user_data['used_hunts']}/{user_data['hunt_limit']}\n⚡️ contract crystals: {user_data['safari_balls']}</b>"
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("contract", callback_data=f"engage_{waifu_id}_{user_id}")]
            ]
        )
        await message.reply_photo(photo=waifu_img_url, caption=text, reply_markup=keyboard, parse_mode='HTML')

        if user_id in current_engagements:
            del current_engagements[user_id]

async def typing_animation(callback_query, text):
    try:
        if random.random() < 0.05:
            duration = 3
        else:
            duration = random.choice([1, 2])

        for i in range(1, duration + 1):
            dots = "⚡️" * i
            await callback_query.message.edit_caption(caption=text + dots)
            await asyncio.sleep(1)

        return dots
    except Exception as e:
        logger.error(f"Error in typing_animation: {e}")
        logger.error(traceback.format_exc())
        return "⚡️⚡️⚡️"  # Fallback to ensure flow continues

async def throw_ball(callback_query):
    user_id = int(callback_query.from_user.id)
    
    async with user_locks[user_id]:
        try:
            data = callback_query.data.split("_")
            waifu_id = data[1]
            user_id = int(data[2])

            if user_id != callback_query.from_user.id:
                await callback_query.answer("This hunt does not belong to you.", show_alert=True)
                return

            if user_id not in safari_users:
                await callback_query.answer("You are not in the safari zone!", show_alert=True)
                return

            if waifu_id not in sessions:
                await callback_query.answer("The wild slave has fled!", show_alert=True)
                return

            user_data = safari_users[user_id]
            user_data['safari_balls'] -= 1
            safari_users[user_id] = user_data

            await save_safari_user(user_id)

            outcome = await typing_animation(callback_query, "𝙔𝙤𝙪 𝙐𝙨𝙚𝙙 𝙊𝙣𝙚 𝘾𝙤𝙣𝙩𝙧𝙖𝙘𝙩 𝘾𝙧𝙮𝙨𝙩𝙖𝙡.\n\n")

            if outcome == "⚡️⚡️⚡️":
                await callback_query.message.edit_caption(caption=f"<b>✨ congratulation ✨\nyou caught the wild slave!</b>", parse_mode="HTML")

                character = sessions[waifu_id]
                await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})

                del sessions[waifu_id]

            else:
                await callback_query.message.edit_caption(caption=f"<b>Your contract crystal failed.</b>\n<b>The wild slave fled.</b>", parse_mode="HTML")
                del sessions[waifu_id]

            if user_data['safari_balls'] <= 0:
                await callback_query.message.edit_caption(caption="You have run out of contract crystals.")
                del safari_users[user_id]
                await safari_users_collection.delete_one({'user_id': user_id})

            del current_hunts[user_id]

        except Exception as e:
            logger.error(f"An error occurred in throw_ball: {e}")
            logger.error(traceback.format_exc())
            await callback_query.answer("An error occurred. Please try again later.", show_alert=True)

async def run_away(callback_query):
    user_id = int(callback_query.from_user.id)
    
    async with user_locks[user_id]:
        try:
            data = callback_query.data.split("_")
            waifu_id = data[1]
            user_id = int(data[2])

            if user_id != callback_query.from_user.id:
                await callback_query.answer("This hunt does not belong to you.", show_alert=True)
                return

            if user_id not in safari_users:
                await callback_query.answer("You are not in the safari zone!", show_alert=True)
                return

            del sessions[waifu_id]
            del current_hunts[user_id]

            await callback_query.message.edit_caption(caption="You escaped from the wild slave.")
            await callback_query.answer()

        except Exception as e:
            print(f"Error handling run_away: {e}")

async def engage(callback_query):
    user_id = int(callback_query.from_user.id)
    
    async with user_locks[user_id]:
        try:
            data = callback_query.data.split("_")
            waifu_id = data[1]
            user_id = int(data[2])

            if user_id != callback_query.from_user.id:
                await callback_query.answer("This hunt does not belong to you.", show_alert=True)
                return

            if user_id not in safari_users:
                await callback_query.answer("You are not in the safari zone!", show_alert=True)
                return

            if waifu_id not in sessions:
                await callback_query.answer("The wild slave has fled!", show_alert=True)
                return

            if user_id in current_engagements:
                del current_engagements[user_id]

            if user_id in current_hunts and current_hunts[user_id] == waifu_id:
                waifu = sessions[waifu_id]
                waifu_name = waifu['name']
                waifu_img_url = waifu['img_url']

                text = f"Choose your action:"
                keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("Throw crystal", callback_data=f"throw_{waifu_id}_{user_id}"),
                            InlineKeyboardButton("Run", callback_data=f"run_{waifu_id}_{user_id}")
                        ]
                    ]
                )
                await callback_query.message.edit_caption(caption=text, reply_markup=keyboard)
                await callback_query.answer()

                current_engagements[user_id] = waifu_id

            else:
                await callback_query.answer("The wild slave has fled!", show_alert=True)

        except Exception as e:
            print(f"Error handling engage: {e}")

async def hunt_callback_query(update: Update, context: CallbackContext):
    callback_query = update.callback_query
    data = callback_query.data.split("_")
    action = data[0]
    waifu_id = data[1]
    user_id = int(data[2])

    if action == "engage":
        await engage(callback_query)
    elif action == "throw":
        await throw_ball(callback_query)
    elif action == "run":
        await run_away(callback_query)

async def dc_command(update: Update, context: CallbackContext):
    # Check if the command is a reply to a message
    if not update.message.reply_to_message:
        await update.message.reply_text("You need to reply to a message to reset that user's cooldown.")
        return
    
    # Extract user_id of the replied user
    replied_user_id = update.message.reply_to_message.from_user.id
    
    # Replace with your authorized user_id
    authorized_user_id = 7011990425
    
    if update.message.from_user.id != authorized_user_id:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    try:
        # Delete the cooldown document for the replied user
        result = await safari_cooldown_collection.delete_one({'user_id': replied_user_id})
        
        if result.deleted_count == 1:
            await update.message.reply_text(f"The tour cooldown for user {replied_user_id} has been reset.")
        else:
            await update.message.reply_text(f"The user {replied_user_id} doesn't have an active tour cooldown.")
    
    except Exception as e:
        print(f"Error resetting safari cooldown for user {replied_user_id}: {e}")
        await update.message.reply_text("An error occurred while resetting the tour cooldown. Please try again later.")
        
application.add_handler(CommandHandler("dc", dc_command))
application.add_handler(CommandHandler("stour", enter_safari))
application.add_handler(CommandHandler("exit", exit_safari))
application.add_handler(CommandHandler("explore", hunt))
application.add_handler(CallbackQueryHandler(hunt_callback_query, pattern="^(engage|throw|run)_", block=False))
