import os
import random
import html
from html import escape
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from shivu import (application, PHOTO_URL, OWNER_ID,
                    user_collection, top_global_groups_collection, top_global_groups_collection, 
                    group_user_totals_collection)

from shivu import sudo_users as SUDO_USERS 

photo = [
    "https://te.legra.ph/file/f95fff0ab4d886b9e7886.jpg",
    "https://te.legra.ph/file/29ea0a82a24168e495aef.jpg",
    "https://te.legra.ph/file/b27c1abc253db724a52fe.jpg",
    "https://te.legra.ph/file/34fd4983b84ba5f35d105.png",
    "https://te.legra.ph/file/698e662682265da4ab256.jpg"
]
    
import random
  
async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>Top 10 Groups:</b>\n───────────────────\n"

    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))

        if len(group_name) > 10:
            group_name = group_name[:15] + '...'
        count = group['count']
        leaderboard_message += f'{i}. <b>{group_name}</b> - {count}\n'

    leaderboard_message += "────────────────────\nTop Groups via @lustXcatcherrobot"

    photo_url = random.choice(photo)

    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')

async def ctop(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$project": {"username": 1, "first_name": 1, "character_count": "$count"}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>Top 10 Users In Chat:</b>\n───────────────────\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> - {character_count}\n'

    leaderboard_message += "────────────────────\nTop User In Chat via @lustXcatcherrobot"

    photo_url = random.choice(photo)

    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')


async def leaderboard(update: Update, context: CallbackContext) -> None:
    # Ensure the characters field exists and is an array
    cursor = user_collection.aggregate([
        {"$match": {"characters": {"$exists": True, "$type": "array"}}},
        {"$project": {"username": 1, "first_name": 1, "character_count": {"$size": "$characters"}}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>Top 10 Users with most slaves:</b>\n───────────────────\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> - <b>{character_count}</b>\n'

    leaderboard_message += "────────────────────\nTop 10 Users via @lustXcatcherrobot"

    # Make sure you have a list named 'photo' with photo URLs
    photo_url = random.choice(photo)

    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')
  
async def send_users_document(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in SUDO_USERS:
        update.message.reply_text('only For Sudo users...')
        return
    cursor = user_collection.find({})
    users = []
    async for document in cursor:
        users.append(document)
    user_list = ""
    for user in users:
        user_list += f"{user['first_name']}\n"
    with open('users.txt', 'w') as f:
        f.write(user_list)
    with open('users.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)
    os.remove('users.txt')

async def send_groups_document(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in SUDO_USERS:
        update.message.reply_text('Only For Sudo users...')
        return
    cursor = top_global_groups_collection.find({})
    groups = []
    async for document in cursor:
        groups.append(document)
    group_list = ""
    for group in groups:
        group_list += f"{group['group_name']}\n"
        group_list += "\n"
    with open('groups.txt', 'w') as f:
        f.write(group_list)
    with open('groups.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)
    os.remove('groups.txt')

async def stats(update: Update, context: CallbackContext) -> None:
    OWNER_ID = 7011990425  # Define your OWNER_ID here

    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    user_count = await user_collection.count_documents({})
    group_count = await group_user_totals_collection.distinct('group_id')

    # Adding 40,000 to the user count and 5,900 to the group count
    adjusted_user_count = user_count + 40000
    adjusted_group_count = len(group_count) + 5900

    await update.message.reply_text(f'Total Users👤: {adjusted_user_count}\nTotal Groups👥: {adjusted_group_count}')



application.add_handler(CommandHandler('topchat', ctop, block=False))
application.add_handler(CommandHandler('TopGroups', global_leaderboard, block=False))
application.add_handler(CommandHandler('stats', stats, block=False))

application.add_handler(CommandHandler('list', send_users_document, block=False))
application.add_handler(CommandHandler('groups', send_groups_document, block=False))


application.add_handler(CommandHandler('gstop', leaderboard, block=False))
