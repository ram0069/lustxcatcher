import random
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from shivu import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from shivu import user_collection, refeer_collection

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username
    args = context.args
    referring_user_id = None
    
    if args and args[0].startswith('r_'):
        referring_user_id = int(args[0][2:])

    user_data = await user_collection.find_one({"id": user_id})

    if user_data is None:
        new_user = {"id": user_id, "first_name": first_name, "username": username, "tokens": 500, "characters": []}
        await user_collection.insert_one(new_user)

        if referring_user_id:
            referring_user_data = await user_collection.find_one({"id": referring_user_id})
            if referring_user_data:
                await user_collection.update_one({"id": referring_user_id}, {"$inc": {"tokens": 1000}})
                referrer_message = f"{first_name} referred you and you got 1000 tokens!"
                try:
                    await context.bot.send_message(chat_id=referring_user_id, text=referrer_message)
                except Exception as e:
                    print(f"Failed to send referral message: {e}")
        
        await context.bot.send_message(chat_id=GROUP_ID, 
                                       text=f"˹ʟᴜꜱᴛ ✘ ᴄᴀᴛᴄʜᴇʀ˼\n#NEWUSER\n User: <a href='tg://user?id={user_id}'>{escape(first_name)}</a>", 
                                       parse_mode='HTML')
    else:
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await user_collection.update_one({"id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    if update.effective_chat.type == "private":
        caption = f"""Hey {first_name}✨\n I'm ˹ʟᴜꜱᴛ ✘ ᴄᴀᴛᴄʜᴇʀ˼. I Am Anime Based Game Bot! Want to get help? Do `/help` !\nWant to request/report bugs? Click on the `Support` button!"""
        
        keyboard = [
            [InlineKeyboardButton(" SUPPORT ", url=f'https://t.me/lustsupport'),
             InlineKeyboardButton(" ADD ME ", url=f'https://t.me/lustXcatcherrobot?startgroup=new')],
            [InlineKeyboardButton(" UPDATE ", url=f'https://t.me/Lustxupdate')],
            [InlineKeyboardButton(" CONTACT ", url=f'https://t.me/WTF_BOOB'),
             InlineKeyboardButton(" SOURCE ", url=f'https://www.youtube.com/watch?v=l1hPRV0_cwc')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        video_url = "https://checker.in/go/10483702"
        await context.bot.send_video(chat_id=update.effective_chat.id, video=video_url, caption=caption, reply_markup=reply_markup, parse_mode='markdown')
    else:
        photo_url = random.choice(PHOTO_URL)
        keyboard = [
            [InlineKeyboardButton("PM", url=f'https://t.me/lustXcatcherrobot?start=true')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        video_url = "https://checker.in/go/10590132"
        await context.bot.send_video(chat_id=update.effective_chat.id, video=video_url, caption=f"""𝙃𝙚𝙮 𝙩𝙝𝙚𝙧𝙚! {first_name}\n\n✨𝙄 𝘼𝙈 𝘼𝙡𝙞𝙫𝙚 𝘽𝙖𝙗𝙮""", reply_markup=reply_markup)

start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)
