from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection
import asyncio
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant, ChatWriteForbidden
from datetime import datetime, timedelta
import random
import time

win_rate_percentage = 5 # Set the win rate percentage here
fight_fee = 200000  # Set the fee for the propose command
user_cooldowns = {}  # Dictionary to track user cooldowns
user_last_command_times = {}  # Dictionary to track user last command times

MUST_JOIN = 'LustxUpdate'
OWNER_ID = 7011990425  # Replace with the actual owner ID

start_messages = [
    "✨ Finally the time has come ✨",
    "💫 The moment you've been waiting for 💫",
    "🌟 The stars align for this proposal 🌟"
]
rejection_captions = [
    "She slapped you and ran away😂",
    "She rejected you outright! 😂",
    "You got a harsh 'NO!' 😂"
]
acceptance_images = [
    "https://te.legra.ph/file/4fe133737bee4866a3549.png",
    "https://te.legra.ph/file/28d46e4656ee2c3e7dd8f.png",
    "https://te.legra.ph/file/d32c6328c6d271dd00816.png"
]
rejection_images = [
    "https://te.legra.ph/file/d6e784e5cda62ac27541f.png",
    "https://te.legra.ph/file/e4e1ba60b4e79359bf9e7.png",
    "https://te.legra.ph/file/81d011398da3a6f49fa7f.png"
]

async def get_random_characters():
    target_rarities = ['🟡 𝙉𝙊𝘽𝙀𝙇', '🥵 𝙉𝙐𝘿𝙀𝙎']  # Example rarities
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

async def log_interaction(user_id):
    # Log user interaction to a specific group
    group_id = -1002057572762  # Set your group ID here
    await bot.send_message(group_id, f"User {user_id} has interacted with the propose command at {time.strftime('%Y-%m-%d %H:%M:%S')}")

@bot.on_message(filters.command(["cd"]))
async def reset_cooldown_command(_: bot, message: t.Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("You do not have permission to use this command.")
    
    if not message.reply_to_message:
        return await message.reply_text("You must reply to a user's message to reset their cooldown.")
    
    target_user_id = message.reply_to_message.from_user.id
    if target_user_id in user_cooldowns:
        user_cooldowns[target_user_id] = 0
        await message.reply_text(f"Cooldown for user {target_user_id} has been reset.")
    else:
        await message.reply_text("The user has no active cooldown.")

@bot.on_message(filters.command(["propose"]))
async def propose_command(_: bot, message: t.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if the user is a member of the required group/channel
    try:
        await bot.get_chat_member(MUST_JOIN, user_id)
    except UserNotParticipant:
        if MUST_JOIN.isalpha():
            link = "https://t.me/" + MUST_JOIN
        else:
            chat_info = await bot.get_chat(MUST_JOIN)
            link = chat_info.invite_link
        try:
            await message.reply_text(
                f"You must join the support group/channel to use this command.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("Join", url=link),
                        ]
                    ]
                ),
                disable_web_page_preview=True
            )
            return
        except ChatWriteForbidden:
            pass

    # Check if the command is used in the allowed group
    allowed_group_id = -1002041586214  # Replace with your allowed group ID
    if chat_id != allowed_group_id:
        return await message.reply_text("This is an exclusive command that only works in @lustsupport")

    current_time = time.time()
    # Check if the user is on cooldown
    if user_id in user_cooldowns and current_time - user_cooldowns[user_id] < 600:  # Adjust cooldown duration
        remaining_time = 600 - (current_time - user_cooldowns[user_id])
        minutes, seconds = divmod(int(remaining_time), 60)
        return await message.reply_text(f"You are still on cooldown. Please wait for `{minutes}:{seconds}` seconds.")

    # Check if the user is spamming commands
    if user_id in user_last_command_times and current_time - user_last_command_times[user_id] < 5:  # Adjust spam threshold
        return await message.reply_text("You are sending commands too quickly. Please wait for a moment.")

    # Update last command time for user
    user_last_command_times[user_id] = current_time

    # Deduct the fight fee from the user's balance
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    user_balance = user_data.get('balance', 0)
    if user_balance < fight_fee:
        return await message.reply_text("You don't have enough tokens to proceed. Need 200,000.")
    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -fight_fee}})

    # Update the user's cooldown
    user_cooldowns[user_id] = current_time

    random_characters = await get_random_characters()
    try:
        # Log user interaction
        await log_interaction(user_id)

        # Initial message with an image
        start_message = random.choice(start_messages)
        photo_path = random.choice(acceptance_images)
        start_msg = await bot.send_photo(chat_id, photo=photo_path, caption=start_message)

        roll_text = random.choice(["Proposing her....💍", "Getting down on one knee....💍", "Popping the question....💍"])
        await message.reply_text(roll_text)

        if random.random() < (win_rate_percentage / 100):
            for character in random_characters:
                try:
                    await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
                except Exception as e:
                    print(e)  # Handle the exception appropriately
            await asyncio.sleep(2)
            img_urls = [character['img_url'] for character in random_characters]
            captions = [
                f"<b>{character['name']}</b> has accepted your proposal! 😇\n"
                f"Slave Name: {character['name']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Anime: {character['anime']}\n"
                for character in random_characters
            ]
            for img_url, caption in zip(img_urls, captions):
                await message.reply_photo(photo=img_url, caption=caption)
        else:
            await asyncio.sleep(2)
            rejection_caption = random.choice(rejection_captions)
            rejection_image = random.choice(rejection_images)
            await message.reply_photo(photo=rejection_image, caption=rejection_caption)
    except Exception as e:
        print(e)
