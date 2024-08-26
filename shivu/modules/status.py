from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from shivu import shivuu
from shivu import SUPPORT_CHAT,user_collection,collection
from shivu import shivuu, SUPPORT_CHAT, user_collection, collection
import os

async def get_user_collection():
    return await user_collection.find({}).to_list(length=None)

async def get_global_rank(user_id: int) -> int:
    pipeline = [
        {"$project": {
            "id": 1,
            "characters_count": {"$cond": {"if": {"$isArray": "$characters"}, "then": {"$size": "$characters"}, "else": 0}}
        }},
        {"$sort": {"characters_count": -1}}
    ]
    
    cursor = user_collection.aggregate(pipeline)
    leaderboard_data = await cursor.to_list(length=None)
    
    for i, user in enumerate(leaderboard_data, start=1):
        if user.get('id') == user_id:
            return i
    
    return 0

async def get_user_balance(user_id: int) -> int:
    user_balance = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    if user_balance:
        return user_balance.get('balance', 0)
    else:
        return 0
    
async def get_user_info(user, already=False):
    if not already:
        user = await shivuu.get_users(user)
    if not user.first_name:
        return ["Deleted account", None]
    
    user_id = user.id
    username = user.username
    existing_user = await user_collection.find_one({'id': user_id})
    first_name = user.first_name
    mention = user.mention("Link")
    global_rank = await get_global_rank(user_id)
    global_count = await collection.count_documents({})
    total_count = len(existing_user.get('characters', []))
    photo_id = user.photo.big_file_id if user.photo else None
    balance = await get_user_balance(user_id)  # New line to fetch user balance
    global_coin_rank = await user_collection.count_documents({'balance': {'$gt': balance}}) + 1
    
    # Check if user has a pass
    if existing_user.get('pass'):
        has_pass = "✅"
    else:
        has_pass = "❌"
    
    # Fetch user's token balance
    tokens = existing_user.get('tokens', 0)
    
    # Format balance and tokens with commas
    balance_formatted = f"{balance:,}"
    tokens_formatted = f"{tokens:,}"
    
    info_text = f"""
「 ✨ 𝙃𝙐𝙉𝙏𝙀𝙍 𝙇𝙄𝘾𝙀𝙉𝙎𝙀 ✨ 」
───────────────────
{first_name}  [`{user_id}`]
𝙐𝙎𝙀𝙍𝙉𝘼𝙈𝙀 : @{username}
───────────────────
𝙎𝙇𝘼𝙑𝙀𝙎 𝗖𝗢𝗨𝗡𝗧 : `{total_count}` / `{global_count}`
𝙂𝙇𝙊𝘽𝘼𝙇 𝙍𝘼𝙉𝙆 : `{global_rank}`
───────────────────
𝙒𝙀𝘼𝙇𝙏𝙃 : ₩`{balance_formatted}`
𝙂𝙇𝙊𝘽𝘼𝙇 𝙒𝙀𝘼𝙇𝙏𝙃 𝙍𝘼𝙉𝙆  : `{global_coin_rank}`
───────────────────
𝙋𝙖𝙨𝙨 : {has_pass}
───────────────────
𝙏𝙊𝙆𝙀𝙉𝙎 : `{tokens_formatted}`
""" 
    return info_text, photo_id

@shivuu.on_message(filters.command("sinfo"))
async def profile(client, message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user.id
    elif not message.reply_to_message and len(message.command) == 1:
        user = message.from_user.id
    elif not message.reply_to_message and len(message.command) != 1:
        user = message.text.split(None, 1)[1]
    existing_user = await user_collection.find_one({'id': user})
    m = await message.reply_text("Geting Your Hunter License..")
    try:
        info_text, photo_id = await get_user_info(user)
    except Exception as e:
        print(f"Something Went Wrong {e}")
        return await m.edit(f"Sorry something Went Wrong Report At @{SUPPORT_CHAT}")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Support",url=f"https://t.me/{SUPPORT_CHAT}")]
    ])
    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Start Me in PM First", url=f"https://t.me/{shivuu.me.username}?start=True")]
        ]
    )
    if photo_id is None:
        return await m.edit(info_text, disable_web_page_preview=True, reply_markup=keyboard)
    elif not existing_user:
        return await m.edit(info_text, disable_web_page_preview=True, reply_markup=reply_markup)
    photo = await shivuu.download_media(photo_id)
    await message.reply_photo(photo, caption=info_text, reply_markup=keyboard)
    await m.delete()
    os.remove(photo)
