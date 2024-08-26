import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection

win_rate_percentage = 30  # Set the win rate percentage here
cooldown_duration = 600  # Set the cooldown duration in seconds
fight_fee = 300000  # Set the fee for the sfight command

user_cooldowns = {}  # Dictionary to track user cooldowns

# List of banned user IDs
ban_user_ids = {1234567890}

async def get_random_characters():
    target_rarities = ['🟡 𝙉𝙊𝘽𝙀𝙇']  # Example rarities
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

@bot.on_message(filters.command(["Sfight"]))
async def sfight(_: bot, message: t.Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id

    receiver_id = message.from_user.id

    # Check if the user is in the ban list
    if user_id in ban_user_ids:
        return await message.reply_text("Sorry, you are banned from this command. go @lustxsupport for help")

    # Check if the user is on cooldown
    if user_id in user_cooldowns and time.time() - user_cooldowns[user_id] < cooldown_duration:
        remaining_time = cooldown_duration - int(time.time() - user_cooldowns[user_id])
        return await message.reply_text(f"Please wait! Your Slaves Are Resting For {remaining_time} seconds.")

    # Deduct the fight fee from the user's balance
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    user_balance = user_data.get('balance', 0)

    if user_balance < fight_fee:
        return await message.reply_text("You don't have enough tokens to initiate a battle. You need at least 300000.")

    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -fight_fee}})

    random_characters = await get_random_characters()

    try:
        # Set the cooldown for the user
        user_cooldowns[user_id] = time.time()

        # Initial message with an image
        start_message = "⚔️ Found A Slave Master Battle Begin 🏹"
        photo_path = 'https://te.legra.ph/file/418e7b7dc070d0bbac096.png'
        start_msg = await bot.send_photo(chat_id, photo=photo_path, caption=start_message)
      
        roll_text = random.choice(["Attacking..."])
        await message.reply_text(roll_text)
        
        if random.random() < (win_rate_percentage / 100):
            for character in random_characters:
                try:
                    await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})
                except Exception as e:
                    print(e)  # Handle the exception appropriately

            await asyncio.sleep(4)

            img_urls = [character['img_url'] for character in random_characters]
            captions = [
                f"You Won🔥! {mention} And Kidnapped One Slave 🌚!\n"
                f"Slave Name: {character['name']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Anime: {character['anime']}\n"
                for character in random_characters
            ]

            for img_url, caption in zip(img_urls, captions):
                await message.reply_photo(photo=img_url, caption=caption)

        else:
            await asyncio.sleep(2)
            await message.reply_text("You Dead. Mar gaya💀☠️")

    except Exception as e:
        print(e)
