from pyrogram import filters, types as t
import random
import time
import asyncio
from pyrogram import Client
from shivu import shivuu, user_collection, registered_users
from shivu import shivuu as bot
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler

cooldown_duration_roll = 30  # 30 seconds

# Dictionary to store the last usage time of the roll command for each user
last_usage_time_roll = {}

# Command to roll the dart
@bot.on_message(filters.command(["dart"]))
async def roll_dart(_: bot, message: t.Message):
    user_id = message.from_user.id
    current_time = time.time()
   
    # Check if the user is registered
    if not await user_collection.find_one({'id': user_id}):
        await message.reply("You need to register first by starting the bot in dm.")
        return

    # Check if the user has used the command recently
    if user_id in last_usage_time_roll:
        time_elapsed = current_time - last_usage_time_roll[user_id]
        remaining_time = max(0, cooldown_duration_roll - time_elapsed)
        if remaining_time > 0:
            return await message.reply_text(f"You're on cooldown. Please wait `{int(remaining_time)}` seconds.")

    command_parts = message.text.split()
    if len(command_parts) != 2:
        return await message.reply_text("Invalid command.\nUsage: `/dart 10000`")
    
    # Get the bet amount from the command
    try:
        dart_amount = int(command_parts[1])
    except ValueError:
        return await message.reply_text("Invalid amount.")
    
    # Get the user's balance
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    if not user_data:
        return await message.reply_text("You don't have enough cash to place this bet.")
    
    # Check if the user has enough tokens to place the bet
    if dart_amount > user_data.get('balance', 0):
        return await message.reply_text("Insufficient balance to place this bet.")

    min_bet_amount = int(user_data['balance'] * 0.07)

    # Check if the amount is greater than or equal to the minimum bet amount
    if dart_amount < min_bet_amount:
        return await message.reply_text(f"Please bet at least `7%` of your balance, which is ₩`{min_bet_amount}`.")
    
    # Roll the dart
    value = await bot.send_dice(chat_id=message.chat.id, emoji="🎯")

    await asyncio.sleep(2)
    if value.dice.value in [4, 5, 6]:
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': dart_amount}})
        win_message = await message.reply_text(f"[🤩](https://te.legra.ph/file/b640e1699912ae19b057f.png) You're lucky!\nYou won ₩`{dart_amount}`")
        # Add XP for winning
        await add_xp(user_id, 4)
    else:
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -dart_amount}})
        lose_message = await message.reply_text(f"[🥲](https://te.legra.ph/file/b640e1699912ae19b057f.png) Better luck next time!\nYou lost ₩`{dart_amount}`")
        # Deduct XP for losing
        await deduct_xp(user_id, 2)

    # Update the last usage time for the user
    last_usage_time_roll[user_id] = current_time

# Function to add XP to a user
async def add_xp(user_id, xp_amount):
    # Update the user's XP in the database
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': xp_amount}}, upsert=True)

# Function to deduct XP from a user
async def deduct_xp(user_id, xp_amount):
    # Update the user's XP in the database
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': -xp_amount}}, upsert=True)
