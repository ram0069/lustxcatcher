import random
from pyrogram import Client, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant, ChatWriteForbidden
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from datetime import datetime, timedelta
from shivu import application, user_collection, collection
from shivu import shivuu as app

MUST_JOIN = "Lactose_edit"  # Replace with your group/channel username or ID
allowed_group_id = -1002041586214  # Replace with your allowed group ID
cooldown_duration = timedelta(days=1)  # Cooldown duration of 24 hours

async def get_random_waifu():
    target_rarities = ['🔵 𝙇𝙊𝙒', '🟢 𝙈𝙀𝘿𝙄𝙐𝙈', '🔴 𝙃𝙄𝙂𝙃', '🟡 𝙉𝙊𝘽𝙀𝙇']
    selected_rarity = random.choice(target_rarities)
    try:
        pipeline = [
            {'$match': {'rarity': selected_rarity}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        waifus = await cursor.to_list(length=None)
        return waifus
    except Exception as e:
        print(e)
        return []

async def claim_waifu(update: Update, context: CallbackContext):
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    mention = f"[{first_name}](tg://user?id={user_id})" if username is None else f"@{username}"

    # Check if the command is used in the allowed group
    if chat_id != allowed_group_id:
        return await message.reply_text("This is an exclusive command that only works in @lustsupport")

    # Check if the user has already claimed the waifu within the cooldown period
    user_data = await user_collection.find_one({'id': user_id}, projection={'last_waifu_claim': 1})
    if user_data and user_data.get('last_waifu_claim'):
        last_claim = user_data['last_waifu_claim']
        if datetime.utcnow() - last_claim < cooldown_duration:
            remaining_time = (cooldown_duration - (datetime.utcnow() - last_claim)).total_seconds()
            hours, remainder = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            return await message.reply_text(f"You can claim your next waifu in {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.")

    try:
        # Check if the user has joined the MUST_JOIN group/channel
        await app.get_chat_member(MUST_JOIN, user_id)
    except UserNotParticipant:
        # If not, prompt the user to join
        if MUST_JOIN.isalpha():
            link = "https://t.me/" + MUST_JOIN
        else:
            chat_info = await app.get_chat(MUST_JOIN)
            link = chat_info.invite_link
        try:
            await message.reply_text(
                "To claim a waifu, you must join the group/channel. Please join and try again.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Join", url=link)]
                    ]
                )
            )
            return
        except ChatWriteForbidden:
            pass

    # Get a random waifu
    waifus = await get_random_waifu()

    if not waifus:
        return await message.reply_text("No waifus available to claim at this moment. Please try again later.")

    waifu = waifus[0]
    
    # Add the waifu to the user's collection and set the cooldown
    await user_collection.update_one(
        {'id': user_id},
        {'$push': {'characters': waifu}, '$set': {'last_waifu_claim': datetime.utcnow()}}
    )

    img_url = waifu['img_url']
    caption = (
        f"{mention} You Got🔥!\n"
        f"Slave Name: {waifu['name']}\n"
        f"Rarity: {waifu['rarity']}\n"
        f"Anime: {waifu['anime']}\n"
    )

    await message.reply_photo(photo=img_url, caption=caption)

application.add_handler(CommandHandler("swaifu", claim_waifu))
