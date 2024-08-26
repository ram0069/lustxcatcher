from pyrogram import Client, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant, ChatWriteForbidden
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from datetime import datetime, timedelta
from shivu import application, user_collection
from shivu import shivuu as app

MUST_JOIN = "DemonSlayer_Update"  # Replace with your group/channel username or ID
allowed_group_id = -1002041586214  # Replace with your allowed group ID

# Additional functionality for rewarding users who claim
async def claim_reward(update: Update, context: CallbackContext):
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if the command is used in the allowed group
    if chat_id != allowed_group_id:
        return await message.reply_text("This is an exclusive command that only works in @lustsupport")

    # Check if the user has already claimed the bonus
    user_data = await user_collection.find_one({'id': user_id}, projection={'eix_suck_claim': 1})
    if user_data and user_data.get('eix_suck_claim', False):
        await message.reply_text("You have already claimed the bonus.")
        return

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
                f"According to my database, you've not joined Support yet. If you want to claim your reward, please join.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("Join", url=link),
                        ]
                    ]
                )
            )
            return
        except ChatWriteForbidden:
            pass

    # If the user has joined the group, grant the yearly reward
    user_data = await user_collection.find_one({'id': user_id})
    if user_data:
        last_claimed_date = user_data.get('eix_suck_claim')

        # Check if a year has passed since the last claim
        if last_claimed_date and datetime.utcnow() - last_claimed_date < timedelta(days=365):
            remaining_time = int((timedelta(days=365) - (datetime.utcnow() - last_claimed_date)).total_seconds())
            await message.reply_text(f"You have already claimed the latest event.")
            return

    # Grant the yearly reward
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': 7500000}, '$set': {'eix_suck_claim': True, 'eix_suck_claim': datetime.utcnow()}}
    )

    # Send the sticker as part of the response
    await message.reply_sticker("CAACAgIAAx0CcyCOBgABAoONZgABHxGFLbz-Zwo7d5qBmRsL8rD_AAJ9AwACbbBCA70TLvm2TbpTNAQ")  # Replace "STICKER_ID_HERE" with the actual sticker ID
    await message.reply_html("<b>Welcome Again😎</b>\n\n<b>Sorry for being inactive for soooo long, here is some bonus for you!😪</b>\n\n<b>Claimed Amount: Ŧ<code>7,500,000</code>.</b>")

application.add_handler(CommandHandler("bonus", claim_reward, block=False))
