import random
import time
import asyncio
from datetime import datetime, timedelta
from pyrogram import filters, types as t
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import shivuu, registered_users, SUPPORT_CHAT
from shivu import shivuu as bot
from shivu import application, user_collection

# Define a dictionary to keep track of cooldowns for each user
cooldowns = {}

# Cooldown duration in seconds
COOLDOWN_DURATION = 10

user_last_command_times = {}

# Mapping of short forms to full forms
CHOICE_MAPPING = {
    "h": "head",
    "t": "tail",
    "head": "head",
    "tail": "tail",
}

async def coin_flip_bet(update: Update, context: CallbackContext):
    message = update.effective_message
    try:
        user_id = message.from_user.id

        # Check if the user is registered
        if not await user_collection.find_one({'id': user_id}):
            await message.reply_text("You need to register first by starting the bot.\nUse: /start", parse_mode='HTML')
            return

        # Check if the correct command format is used
        if len(message.text.split()) != 3:
            await message.reply_text("Usage: `/sbet 10000 t`", parse_mode='HTML')
            return

        # Check if the user is still in cooldown
        if user_id in cooldowns and (time.time() - cooldowns[user_id]) < COOLDOWN_DURATION:
            remaining_time = int(COOLDOWN_DURATION - (time.time() - cooldowns[user_id]))
            await message.reply_text(f"Please wait {remaining_time} seconds before using /sbet again.", parse_mode='HTML')
            return

        # Extract the bet amount and choice from the command
        try:
            _, bet_amount_str, bet_choice_short = message.text.split()
            bet_amount = int(bet_amount_str)
            bet_choice = CHOICE_MAPPING.get(bet_choice_short.lower())
        except ValueError:
            await message.reply_text("Invalid bet amount. Please use a numerical value.", parse_mode='HTML')
            return

        # Check if the user's choice is either "head" or "tail"
        if bet_choice not in ["head", "tail"]:
            await message.reply_text("Invalid choice. Please use `/sbet 10000 t`.", parse_mode='HTML')
            return

        # Check if the user has sufficient balance for the bet
        user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})

        if not user_data or user_data.get('balance', 0) < bet_amount:
            await message.reply_text("Insufficient balance for the bet.", parse_mode='HTML')
            return

        # Check if the user is betting more than 7% of their balance
        seven_percent_value = int(0.07 * user_data['balance'])
        if bet_amount < seven_percent_value:
            await message.reply_text(f"Please bet at least `7%` of your balance, which is ₩<code>{seven_percent_value}</code>.", parse_mode='HTML')
            return

        # Perform the coin flip
        coin_result = random.choice(["head", "tail"])

        # Check if the user's choice matches the coin flip result
        if bet_choice == coin_result:
            # User wins the bet
            await user_collection.update_one({'id': user_id}, {'$inc': {'balance': bet_amount}})
            await message.reply_text(f"[🤩](https://te.legra.ph/file/f4b3c103015f81aa82914.png) You chose <code>{bet_choice}</code>\nYou won ₩<code>{bet_amount}</code>.", parse_mode='HTML')
            # Add XP for winning
            await add_xp(user_id, 4)
        else:
            # User loses the bet
            await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -bet_amount}})
            await message.reply_text(f"[🥲](https://te.legra.ph/file/f4b3c103015f81aa82914.png) You chose <code>{bet_choice}</code>\nYou lost ₩<code>{bet_amount}</code>.", parse_mode='HTML')
            # Deduct XP for losing
            await deduct_xp(user_id, 2)

        # Set the cooldown time for the user
        cooldowns[user_id] = time.time()

    except Exception as e:
        print(f"Error: {e}")

# Function to add XP to a user
async def add_xp(user_id, xp_amount):
    # Update the user's XP in the database
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': xp_amount}}, upsert=True)

# Function to deduct XP from a user
async def deduct_xp(user_id, xp_amount):
    # Update the user's XP in the database
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': -xp_amount}}, upsert=True)

# Define the cooldown duration
cooldown_duration_roll = 30  # 30 seconds

# Dictionary to store the last usage time of the roll command for each user
last_usage_time_roll = {}

# Command to roll the dice
async def roll_dice(update: Update, context: CallbackContext):
    message = update.effective_message
    user_id = message.from_user.id
    current_time = time.time()

    # Check if the user is registered
    if not await user_collection.find_one({'id': user_id}):
        await message.reply_text("You need to register first by starting the bot.\nUse: /start", parse_mode='HTML')
        return

    # Check if the user has used the command recently
    if user_id in last_usage_time_roll:
        time_elapsed = current_time - last_usage_time_roll[user_id]
        remaining_time = max(0, cooldown_duration_roll - time_elapsed)
        if remaining_time > 0:
            return await message.reply_text(f"You're on cooldown. Please wait {int(remaining_time)} seconds before using this command again.", parse_mode='HTML')

    command_parts = message.text.split()
    if len(command_parts) != 3:
        return await message.reply_text("Invalid command.\nUsage: `/roll 1000 odd`", parse_mode='HTML')

    # Get the amount and bet type (odd/even) from the command
    try:
        _, amount_str, bet_type = command_parts
        amount = int(amount_str)
        bet_type = bet_type.lower()
    except ValueError:
        return await message.reply_text("Invalid amount.", parse_mode='HTML')

    # Check if the bet type is either odd or even
    if bet_type not in ['odd', 'even']:
        return await message.reply_text("You have to choose either odd or even.", parse_mode='HTML')

    # Get the user's token balance
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    if not user_data:
        return await message.reply_text("You don't have enough tokens to place this bet.", parse_mode='HTML')

    # Calculate the minimum bet amount (7% of the user's balance)
    min_bet_amount = int(user_data['balance'] * 0.07)

    # Check if the amount is greater than or equal to the minimum bet amount
    if amount < min_bet_amount:
        return await message.reply_text(f"Please bet at least `7%` of your balance, which is ₩<code>{min_bet_amount}</code>.", parse_mode='HTML')

    if user_data.get('balance', 0) < amount:
        return await message.reply_text("You don't have enough tokens to place this bet.", parse_mode='HTML')

    # Roll the dice
    xx = await bot.send_dice(chat_id=message.chat.id)
    value = int(xx.dice.value)

    # Introduce a delay of 3 seconds before sending the win or loss message
    await asyncio.sleep(3)

    # Determine if the user won or lost
    if (value % 2 == 0 and bet_type == 'even') or (value % 2 != 0 and bet_type == 'odd'):
        # User wins
        # Update user's balance
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': amount}})
        await message.reply_text(f"[🤩](https://te.legra.ph/file/f62370f51e71813ceee75.png) The dice rolled at {'Even' if value % 2 == 0 else 'Odd'} digit!\n\nYou won ₩<code>{amount}</code>.", parse_mode='HTML')
        # Add XP for winning
        await add_xp(user_id, 4)
    else:
        # User loses
        # Update user's balance
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -amount}})
        await message.reply_text(f"[🥲](https://te.legra.ph/file/f62370f51e71813ceee75.png) The dice rolled at {'Even' if value % 2 == 0 else 'Odd'} digit!\n\nYou lost ₩<code>{amount}</code>.", parse_mode='HTML')
        # Deduct XP for losing
        await deduct_xp(user_id, 2)

    # Update the last usage time for the user
    last_usage_time_roll[user_id] = current_time

application.add_handler(CommandHandler('sbet', coin_flip_bet, block=False))
application.add_handler(CommandHandler('roll', roll_dice, block=False))
