from pyrogram import filters, types as t
import random
import time
import asyncio
from pyrogram import Client
from shivu import shivuu, user_collection, registered_users
from shivu import shivuu as bot

# Cooldown duration for the lever command in seconds
cooldown_duration_roll = 600

# Dictionary to store the last usage time of the roll command for each user
last_usage_time_roll = {}

# Command to roll the dart
@bot.on_message(filters.command(["lever"]))
async def roll_dart(_, message: t.Message):
    user_id = message.from_user.id
    current_time = time.time()

    # Check if the user is registered
    if not await user_collection.find_one({'id': user_id}):
        await message.reply("You need to register first by starting the bot in dm.")
        return

    command_parts = message.text.split()
    if len(command_parts) != 2:
        return await message.reply_text("Invalid command.\nUsage: `/lever 99999`")

    # Get the bet amount from the command
    try:
        slot_amount = int(command_parts[1])
    except ValueError:
        return await message.reply_text("Invalid amount.")

    # Get the user's balance
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    if not user_data:
        return await message.reply_text("You don't have enough cash to place this bet.")

    # Check if the user has enough tokens to place the bet
    if slot_amount > user_data.get('balance', 0):
        return await message.reply_text("Insufficient cash to place this bet.")

    min_bet_amount = int(user_data['balance'] * 0.07)

    # Check if the amount is greater than or equal to the minimum bet amount
    if slot_amount < min_bet_amount:
        return await message.reply_text(f"Please bet at least `7%` of your balance, which is ₩`{min_bet_amount}`.")

    max_bet_amount = int(user_data['balance'] * 0.4)
    if slot_amount > max_bet_amount:
        return await message.reply_text(f"can't bet more than`40%` of your balance, which is ₩`{max_bet_amount}`.")


    # Check if the user has used the command recently
    if user_id in last_usage_time_roll:
        time_elapsed = current_time - last_usage_time_roll[user_id]
        remaining_time = max(0, cooldown_duration_roll - time_elapsed)
        if remaining_time > 0:
            return await message.reply_text(f"You're on cooldown. Please wait `{int(remaining_time)}` seconds.")

    # Update the last usage time of the command for the user
    last_usage_time_roll[user_id] = current_time

    # Roll the dice
    value = await bot.send_dice(chat_id=message.chat.id, emoji="🎰")
    await asyncio.sleep(random.uniform(1, 5))
    slot_value = value.dice.value

    # Define the reward multipliers
    jackpot_multiplier = 2
    two_equal_multiplier = 1

    # Check the slot machine result
    if slot_value in (1, 22, 43, 64):
        reward = jackpot_multiplier * slot_amount
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': reward}})
        await message.reply_text(f"[🤩](https://te.legra.ph/file/b5fbf9f4b64ea9baf6845.png) You hit the jackpot!\nYou won ₩`{reward}`!")
        await add_xp(user_id, 6)
    elif slot_value in (2, 3, 4, 5, 6, 9, 11, 13, 16, 17, 18, 21, 23, 24, 26, 27, 30, 32, 33, 35, 38, 39, 41, 42, 44, 47, 48, 49, 52, 54, 56, 59, 60, 61, 62, 63):
        reward = two_equal_multiplier * slot_amount
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': reward}})
        await message.reply_text(f"[🤩](https://te.legra.ph/file/b5fbf9f4b64ea9baf6845.png)Two signs came out equal!\nYou won ₩`{reward}`!")
        await add_xp(user_id, 4)
    else:
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -slot_amount}})
        await message.reply_text(f"[🥲](https://te.legra.ph/file/b5fbf9f4b64ea9baf6845.png) Nothing got matched!\nYou lost ₩`{slot_amount}`.")
        await deduct_xp(user_id, 2)


async def add_xp(user_id, xp_amount):
    # Update the user's XP in the database
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': xp_amount}}, upsert=True)

# Function to deduct XP from a user
async def deduct_xp(user_id, xp_amount):
    # Update the user's XP in the database
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': -xp_amount}}, upsert=True)
