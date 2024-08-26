from pyrogram import filters, types as t
import random
import time
import asyncio
from pyrogram import Client
from shivu import application, user_collection
from shivu import shivuu as bot
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

cooldown_duration_roll = 30  # 30 seconds

# Dictionary to store the last usage time of the roll command for each user
last_usage_time_roll = {}

# Command to roll the dart
async def roll_dart(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    current_time = time.time()

    # Check if the user is registered
    if not await user_collection.find_one({'id': user_id}):
        await update.message.reply_text("You need to register first by starting the bot in dm.", parse_mode='HTML')
        return

    # Check if the user has used the command recently
    if user_id in last_usage_time_roll:
        time_elapsed = current_time - last_usage_time_roll[user_id]
        remaining_time = max(0, cooldown_duration_roll - time_elapsed)
        if remaining_time > 0:
            await update.message.reply_text(f"You're on cooldown. Please wait `{int(remaining_time)}` seconds.", parse_mode='HTML')
            return

    command_parts = update.message.text.split()
    if len(command_parts) != 2:
        await update.message.reply_text("Invalid command.\nUsage: `/basket 10000`", parse_mode='HTML')
        return

    # Get the bet amount from the command
    try:
        bastek_amount = int(command_parts[1])
    except ValueError:
        await update.message.reply_text("Invalid amount.", parse_mode='HTML')
        return

    # Get the user's balance
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    if not user_data:
        await update.message.reply_text("You don't have enough cash to place this bet.", parse_mode='HTML')
        return

    # Check if the user has enough tokens to place the bet
    if bastek_amount > user_data.get('balance', 0):
        await update.message.reply_text("Insufficient balance to place this bet.", parse_mode='HTML')
        return

    min_bet_amount = int(user_data['balance'] * 0.07)

    # Check if the amount is greater than or equal to the minimum bet amount
    if bastek_amount < min_bet_amount:
        await update.message.reply_text(f"Please bet at least `7%` of your balance, which is ₩`{min_bet_amount}`.", parse_mode='HTML')
        return

    # Roll the dart
    value = await bot.send_dice(chat_id=update.effective_chat.id, emoji="🏀")

    await asyncio.sleep(2)
    if value.dice.value in [4, 5, 6]:
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': bastek_amount}})
        await update.message.reply_text(f"[🤩](https://te.legra.ph/file/95755bb1f869843b3f309.png) You're lucky!\nYou won ₩<code>{bastek_amount}</code>", parse_mode='HTML')
        # Add XP for winning
        await add_xp(user_id, 4)
    else:
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -bastek_amount}})
        await update.message.reply_text(f"[🥲](https://te.legra.ph/file/95755bb1f869843b3f309.png) Better luck next time!\nYou lost ₩<code>{bastek_amount}</code>", parse_mode='HTML')
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

# Add the handler to the application
basket_handler = CommandHandler("basket", roll_dart)
