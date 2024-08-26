from telegram.ext import CommandHandler
from shivu import application, registered_users,SUPPORT_CHAT
from telegram import Update
from datetime import datetime, timedelta
import asyncio
import time
import random
import html
from datetime import datetime, timedelta
from shivu import shivuu as bot
from shivu import shivuu as app
from pyrogram.types import Message
from pyrogram import filters, types as t
from html import escape
from shivu import application, user_collection
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from shivu import sudo_users_collection, user_collection
from shivu.modules.database.sudo import is_user_sudo

cooldowns = {}
ban_user_ids = {5553813115}
logs_group_id = -1001992547604
logs = {logs_group_id}
async def send_start_button(chat_id):
    await app.send_message(chat_id, "You need to register first by starting the bot in dm.")
    
@app.on_message(filters.command(["sinv", "balance", "bal", "wealth"]))
async def check_balance(_, message: Message):
    user_id = message.from_user.id
    replied_user_id = None
    
    if message.reply_to_message:
        replied_user_id = message.reply_to_message.from_user.id
    
    # Check if the command was used as a reply
    if replied_user_id:
        user_id = replied_user_id
    
    # Check if the user is registered
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await send_start_button(message.chat.id)
        return
    balance = user_data.get('balance', 0)
    formatted_balance = "{:,.0f}".format(balance)
    first_name = user_data.get('first_name', 'User')
    # Reply to the user with their balance
    await message.reply_text(f"{first_name}'s Wealth: ₩`{formatted_balance}`[.](https://te.legra.ph/file/552111e23c19f694f50e4.png)")
    
async def pay(update, context):
    sender_id = update.effective_user.id
    keyboard = [[InlineKeyboardButton("APPEAL", url=f'https://t.me/lustsupport')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Check if the user is still in cooldown
    if sender_id in cooldowns and (time.time() - cooldowns[sender_id]) < 1200:
        remaining_time = int(1200 - (time.time() - cooldowns[sender_id]))
        await update.message.reply_text(f"Please wait {remaining_time // 60} minutes and {remaining_time % 60} seconds before using /pay again.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a user to /pay.")
        return
    recipient_id = update.message.reply_to_message.from_user.id
    
    try:
        amount = int(context.args[0])
        # Check if the amount is negative
        if amount < 0:
            raise ValueError("Negative amounts are not allowed.")
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid amount. Usage: /pay <amount>")
        return
    # Check if the amount is greater than 1,000,000,000
    if amount > 1000000000:
        await update.message.reply_text("Can't pay more than 1,000,000,000.")
        return
    sender_balance = await user_collection.find_one({'id': sender_id}, projection={'balance': 1})
    if not sender_balance or sender_balance.get('balance', 0) < amount:
        await update.message.reply_text("Insufficient balance to make the payment.")
        return
    disallowed_words = ['negative', 'badword']  # Add your disallowed words here
    payment_message = update.message.text.lower()
    if any(word in payment_message for word in disallowed_words):
        await update.message.reply_text("Sorry, your payment message contains disallowed words.")
        return
    await user_collection.update_one({'id': sender_id}, {'$inc': {'balance': -amount}})
    await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': amount}})
    await update.message.reply_text(
        f"₩ Payment Successful! You paid ₩{amount} cash to {update.message.reply_to_message.from_user.first_name}."
    )
    # Set the cooldown time for the user
    cooldowns[sender_id] = time.time()
    # Log payment information
    logs_message = f"🔄 Payment Log\nSender: {update.effective_user.username} (ID: {sender_id})\nAmount: {amount} TOK\nRecipient: {update.message.reply_to_message.from_user.username} (ID: {recipient_id})"
    
    for log_group_id in logs:
        try:
            await context.bot.send_message(log_group_id, logs_message)
        except Exception as e:
            print(f"Error sending payment log to group {log_group_id}: {str(e)}")
            
async def mtop(update, context):
    top_users = await user_collection.find({}, projection={'id': 1, 'first_name': 1, 'last_name': 1, 'balance': 1}).sort('balance', -1).limit(10).to_list(10)
    top_users_message = "Top 10 Wealthy Users:\n───────────────────\n"
    for i, user in enumerate(top_users, start=1):
        first_name = user.get('first_name', 'Unknown')
        last_name = user.get('last_name', '')
        username = user.get('username', 'Unknown')
        user_id = user.get('id', 'Unknown')
        full_name = f"{first_name} {last_name}" if last_name else first_name
        user_link = f"<a href='tg://user?id={user_id}'>{html.escape(first_name)}</a>"
        top_users_message += f"{i}. {user_link} - ₩{user.get('balance', 0):,.0f}\n"
    top_users_message += "────────────────────\nTop 10 Wealthy Users via @lustXcatcherrobot"
    photo_path = 'https://te.legra.ph/file/29ea0a82a24168e495aef.jpg'
    await update.message.reply_photo(photo=photo_path, caption=top_users_message, parse_mode='HTML')
            
@bot.on_message(filters.command("daily"))
async def daily_reward(_, message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'last_daily_reward': 1, 'balance': 1})
    if not user_data:
        await send_start_button(message.chat.id)
        return
    last_claimed_date = user_data.get('last_daily_reward')
    if last_claimed_date and last_claimed_date.date() == datetime.utcnow().date():
        await message.reply_text("You've already claimed your daily reward today. Come back tomorrow!")
        return
    # Update the user's balance and set the last claimed date to today
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': 50000}, '$set': {'last_daily_reward': datetime.utcnow()}}
    )
    await message.reply_text("❰ 𝗥 𝗘 𝗪 𝗔 𝗥 𝗗 𝗦 🧧 ❱\n\n◍ Daily reward claimed successfully!\nYou gained ₩`50,000`")
    
@bot.on_message(filters.command("weekly"))
async def weekly_reward(_, message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'last_weekly_reward': 7, 'balance': 1})
    if not user_data:
        await send_start_button(message.chat.id)
        return
    last_weekly_date = user_data.get('last_weekly_reward')
    if last_weekly_date and last_weekly_date.date() == datetime.utcnow().date():
        await message.reply_text("You've already claimed your weekly reward of this week.")
        return
    # Update the user's balance and set the last claimed date to today
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': 250000}, '$set': {'last_weekly_reward': datetime.utcnow()}}
    )
    await message.reply_text("❰ 𝗥 𝗘 𝗪 𝗔 𝗥 𝗗 𝗦 🧧 ❱\n\n◍ Weekly reward claimed successfully!\nYou gained ₩`250,000`")
    
user_last_command_times = {}
@bot.on_message(filters.command("tesure"))
async def daily_reward(_, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name.strip()
    last_name = message.from_user.last_name.strip() if message.from_user.last_name else ""
    current_time = datetime.utcnow()
    # Check if the user is sending commands too quickly
    if user_id in user_last_command_times and (current_time - user_last_command_times[user_id]).total_seconds() < 5:  # 5 seconds threshold
        await message.reply_text("You are sending commands too quickly. Please wait for a moment.")
        return
    # Update the last command time
    user_last_command_times[user_id] = current_time
    print(f"Debug: User's first name is '{first_name}', last name is '{last_name}'")  # Debug statement
    # Check for specific tags in both first name and last name
    if "बदमोस" not in first_name and "बदमोस" not in last_name:
        await message.reply_text("Plz set `बदमोस` in your first or last name to use this command.")
        return
    if "𝘿𝙍𝘼𝙂𝙊𝙉𝙎⃟🐉" in first_name or "𝘿𝙍𝘼𝙂𝙊𝙉𝙎⃟🐉" in last_name:
        await message.reply_text("Plz remove other tags `𝘿𝙍𝘼𝙂𝙊𝙉𝙎⃟🐉` and only use `बदमोस` in your first or last name to use this command.")
        return
    user_data = await user_collection.find_one({'id': user_id}, projection={'last_tesure_reward': 1, 'balance': 1})
    if not user_data:
        await send_start_button(message.chat.id)
        return
    last_claimed_time = user_data.get('last_tesure_reward')
    if last_claimed_time:
        last_claimed_time = last_claimed_time.replace(tzinfo=None)
    if last_claimed_time and (current_time - last_claimed_time) < timedelta(minutes=30):
        remaining_time = timedelta(minutes=30) - (current_time - last_claimed_time)
        minutes, seconds = divmod(remaining_time.seconds, 60)
        await message.reply_text(f"Try again in `{minutes}:{seconds}` seconds.")
        return
    # Generate a random reward between 5,000,000 and 10,000,000
    reward = random.randint(5000000, 10000000)
    # Update the user's balance and set the last claimed time to now
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': reward}, '$set': {'last_tesure_reward': current_time}}
    )
    await message.reply_text(f"❰ 𝗧 𝗥 𝗘 𝗔 𝗦 𝗨 𝗥 𝗘 🧧 ❱\n\n◍ Tesure claimed successfully!\nYou gained ₩`{reward:,}`[.](https://te.legra.ph/file/660ae74763876ceb19f34.png)")

application.add_handler(CommandHandler("tops", mtop, block=False))
application.add_handler(CommandHandler("pay", pay, block=False))

    
async def add_tokens(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if the user is a sudo user
    if not await is_user_sudo(user_id):
        await update.message.reply_text("You don't have permission to add tokens.")
        return

    # Check if the command includes the required arguments
    if len(context.args) != 2:
        await update.message.reply_text("Invalid usage. Usage: /addt <user_id> <amount>")
        return

    target_user_id = int(context.args[0])
    amount = int(context.args[1])

    # Find the target user
    target_user = await user_collection.find_one({'id': target_user_id})
    if not target_user:
        await update.message.reply_text("User not found.")
        return

    # Update the balance by adding tokens
    new_balance = target_user.get('balance', 0) + amount
    await user_collection.update_one({'id': target_user_id}, {'$set': {'balance': new_balance}})
    await update.message.reply_text(f"Added {amount} tokens to user {target_user_id}. New balance: {new_balance}")

async def delete_tokens(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if the user is a sudo user
    if not await is_user_sudo(user_id):
        await update.message.reply_text("You don't have permission to delete tokens.")
        return

    # Check if the command includes the required arguments
    if len(context.args) != 2:
        await update.message.reply_text("Invalid usage. Usage: /delt <user_id> <amount>")
        return

    target_user_id = int(context.args[0])
    amount = int(context.args[1])

    # Find the target user
    target_user = await user_collection.find_one({'id': target_user_id})
    if not target_user:
        await update.message.reply_text("User not found.")
        return

    # Check if there are enough tokens to delete
    current_balance = target_user.get('balance', 0)
    if current_balance < amount:
        await update.message.reply_text("Insufficient tokens to delete.")
        return

    # Update the balance by deleting tokens
    new_balance = current_balance - amount
    await user_collection.update_one({'id': target_user_id}, {'$set': {'balance': new_balance}})
    await update.message.reply_text(f"Deleted {amount} tokens from user {target_user_id}. New balance: {new_balance}")

application.add_handler(CommandHandler("addt", add_tokens, block=False))
application.add_handler(CommandHandler("delt", delete_tokens, block=False))

async def reset_tokens(update, context):
    owner_id = 7011990425  # Replace with the actual owner's user ID
    # Check if the user invoking the command is the owner
    if update.effective_user.id != owner_id:
        await update.message.reply_text("You don't have permission to perform this action.")
        return
    # Reset tokens for all users
    await user_collection.update_many({}, {'$set': {'balance': 10000}})
    
    await update.message.reply_text("All user tokens have been reset to 10,000.")
# Add a handler for the /reset_tokens command
application.add_handler(CommandHandler("reset", reset_tokens, block=False))
