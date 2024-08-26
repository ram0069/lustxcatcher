from pyrogram import Client, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, Message
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
import random
from datetime import datetime, timedelta
from shivu import user_collection, application

active_games = {}
user_cooldowns = {}

MAX_BET_AMOUNT = 100_000_000_000  # Maximum bet amount of 100 million

photo = [
    "https://telegra.ph/file/6d8417aa0efb0abc57eb6.png",
    "https://telegra.ph/file/6f92ca5aab1c49fe68bcf.png",
    "https://telegra.ph/file/c10dcf612ddb383cf5fee.png",
    "https://telegra.ph/file/66488042b1fe9cd789a90.png",
    "https://telegra.ph/file/ca75337e97fb1f5f64c37.png",
    "https://telegra.ph/file/bbfb952b9b996e9279101.png"
]

async def start_gamble_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id  # Get the user ID
    current_time = datetime.now()
    message = update.message.text.split()

    if not await user_collection.find_one({'id': user_id}):
        await message.reply("You need to register first by starting the bot in dm.")
        return

    if len(message) < 2:
        await update.message.reply_text("Usage: /gamble <amount>")
        return

    try:
        bet_amount = int(message[1])
    except ValueError:
        await update.message.reply_text("Invalid bet amount. Please enter a number.")
        return

    # Check if the bet amount exceeds the maximum limit
    if bet_amount > MAX_BET_AMOUNT:
        await update.message.reply_text(f"The maximum bet amount is ₩{MAX_BET_AMOUNT}. Please enter a lower amount.")
        return

    # Check if the user is on cooldown
    if user_id in user_cooldowns and current_time < user_cooldowns[user_id]:
        remaining_time = (user_cooldowns[user_id] - current_time).total_seconds()
        await update.message.reply_html(f"Please wait <code>{int(remaining_time)}</code> seconds before starting a new game.")
        return

    # Check user tokens
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data or user_data['balance'] < bet_amount:
        await update.message.reply_text(f"{update.effective_user.first_name}, you don't have enough tokens to place this bet.")
        return

    # Deduct the bet amount from user's balance
    new_balance = user_data['balance'] - bet_amount
    await user_collection.update_one({'id': user_id}, {'$set': {'balance': new_balance}})

    # Store the bet amount in active games
    active_games[user_id] = {
        'bet_amount': bet_amount,
        'start_time': current_time,
        'user_id': user_id,
    }

    # Send image and ask user to choose left or right
    image_url = random.choice(photo)  # Replace with your image URL
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Left", callback_data=f'guess_{user_id}_left'), InlineKeyboardButton("Right", callback_data=f'guess_{user_id}_right')]
    ])
    await update.message.reply_photo(photo=image_url, caption="Guess in which hand the coin is hidden:", reply_markup=keyboard)
    
async def guess_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split('_')
    action = data[0]
    game_user_id = int(data[1])
    guess = data[2]

    if game_user_id not in active_games:
        await query.answer("No active game found.", show_alert=True)
        return

    if user_id != game_user_id:
        await query.answer("You are not allowed to make this guess.", show_alert=True)
        return

    game = active_games[game_user_id]
    bet_amount = game['bet_amount']

    # Simulate the coin being in the left or right hand
    correct_hand = random.choice(['left', 'right'])

    if guess == correct_hand:
        result_message = f"😈<b> You chose </b><code>{guess}</code><b> and won </b>₩<code>{bet_amount}</code>."
        new_balance = bet_amount * 2
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': new_balance}})
    else:
        result_message = f"🥲<b> You chose </b><code>{guess}</code><b> and lost </b>₩<code>{bet_amount}</code>."

    # Set user cooldown for 10 seconds
    user_cooldowns[user_id] = datetime.now() + timedelta(seconds=10)

    # Edit the message text with the result
    await query.message.edit_caption(result_message, parse_mode='HTML')

    # Remove the game from active games
    del active_games[game_user_id]

application.add_handler(CommandHandler('gamble', start_gamble_cmd, block=False))
application.add_handler(CallbackQueryHandler(guess_callback, pattern=r'^guess_\d+_(left|right)$', block=False))
