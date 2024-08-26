from pyrogram import filters
from shivu import application, user_collection
from shivu import shivuu as bot
from pyrogram.types import Message
from html import escape
from telegram.ext import CommandHandler


XP_PER_LEVEL = 40

# Level titles
LEVEL_TITLES = {
    (0, 10): "👤 Rokki",  
    (11, 30): "🌟 F",
    (31, 50): "⚡️ E",
    (51, 75): "🔫 D",
    (76, 100): "🛡 C",
    (101, 125): "🗡 B",
    (126, 150): "⚔️ A",
    (151, 175): "🎖 S",
    (176, 200): "🔱 National",
    (201, 2000): "👑 MOnarch",
    # Add more level ranges and titles as needed
}
def calculate_level(xp):
    return xp // XP_PER_LEVEL

def get_user_level_title(user_level):
    for level_range, title in LEVEL_TITLES.items():
        if level_range[0] <= user_level <= level_range[1]:
            return title
    return "`👤 Rokki`"
# Command to check XP and level
@bot.on_message(filters.command(["xp"]))
async def check_stats(_, message: Message):
    user_id = message.from_user.id
    replied_user_id = None
    
    if message.reply_to_message:
        replied_user_id = message.reply_to_message.from_user.id
    
    # Check if the command was used as a reply
    if replied_user_id:
        user_id = replied_user_id
    
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        return await message.reply_text("You need to grab slave first.")
    
    # Fetch user's XP from the database
    user_xp_data = await user_collection.find_one({'id': user_id})
    if user_xp_data:
        user_xp = user_xp_data.get('xp', 0)
        # Calculate user's level
        user_level = user_xp // XP_PER_LEVEL

        # Get user's level title
        user_level_title = get_user_level_title(user_level)
        first_name = user_data.get('first_name', 'User')

        await message.reply_text(f"{first_name} is a {user_level_title} rank at level {user_level} with {user_xp} XP.")
    else:
        await message.reply_text("You don't have any XP yet.")

async def xtop(update, context):
    top_users = await user_collection.find({}, projection={'id': 1, 'first_name': 1, 'last_name': 1, 'xp': 1}).sort('xp', -1).limit(10).to_list(10)

    top_users_message = "Top 10 Xp Users:\n───────────────────\n"
    for i, user in enumerate(top_users, start=1):
        first_name = user.get('first_name', 'Unknown')
        last_name = user.get('last_name', '')
        username = user.get('username', 'Unknown')
        user_id = user.get('id', 'Unknown')

        full_name = f"{first_name} {last_name}" if last_name else first_name

        user_link = f"<a href='tg://user?id={user_id}'>{(escape(first_name))}</a>"

        top_users_message += f"{i}. {user_link} - ( {user.get('xp', 0):,.0f} xp)\n"

    top_users_message += "────────────────────\nTop 10 Users via @lustXcatcherrobot"

    photo_path = 'https://graph.org/file/c6fefec4aab0367ad5f63.jpg'
    await update.message.reply_photo(photo=photo_path, caption=top_users_message, parse_mode='HTML')

application.add_handler(CommandHandler("xtop", xtop, block=False))
