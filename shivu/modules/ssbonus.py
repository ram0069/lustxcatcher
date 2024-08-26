from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant, ChatWriteForbidden
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext
from datetime import datetime
from shivu import application, user_collection
from shivu import shivuu as app

MUST_JOIN = "slave_update"  # Replace "lust_support" with your group/channel username or ID
allowed_group_id = -1002041586214  # Replace with your allowed group ID

async def claim_reset_bonus(update: Update, context: CallbackContext):
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id != allowed_group_id:
        return await message.reply_text("This is an exclusive command that only works in @lustsupport")

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
                f"To claim the reset bonus, you must join the group/channel. Please join and try again.",
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

    # Check if the user has already claimed the bonus
    user_data = await user_collection.find_one({'id': user_id}, projection={'shith_suck_bonus': 1})
    if user_data and user_data.get('shith_suck_bonus'):
        await message.reply_text("You have already claimed the reset bonus.")
        return

    # Grant the reset bonus
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': 30000000}, '$set': {'shith_suck_bonus': datetime.utcnow()}}
    )

    # Send the sticker as part of the response
    await message.reply_sticker("CAACAgIAAx0CcyCOBgABAoONZgABHxGFLbz-Zwo7d5qBmRsL8rD_AAJ9AwACbbBCA70TLvm2TbpTNAQ")  # Replace "STICKER_ID_HERE" with the actual sticker ID 
    await message.reply_html("<b>Welcome Again😎</b>\n\n<b>Sorry for Token reset, here is some bonus for you!😪</b>\n\n<b>Claimed Amount: <code>30,000,000</code>.</b>")

application.add_handler(CommandHandler("sbonus", claim_reset_bonus, block=False))
