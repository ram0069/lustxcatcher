import importlib
import time
import random
import re
import os
import asyncio
from html import escape 
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from shivu import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, shivuu
from shivu import application, LOGGER, TOKEN 
from shivu import set_on_data, set_off_data
from shivu.modules import ALL_MODULES
locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}
group_rarity_percentages = {}
for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)
    
last_user = {}
warned_users = {}
def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)
  
archived_characters = {}
ran_away_count = {}
async def ran_away(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    if chat_id in last_characters:
        if chat_id not in ran_away_count:
            ran_away_count[chat_id] = 0
        ran_away_count[chat_id] += 1
        character_data = last_characters[chat_id]
        character_name = character_data['name']
        if ran_away_count[chat_id] > 15:
            if chat_id in first_correct_guesses:
                if chat_id in ran_away_count:
                    del ran_away_count[chat_id]
            else:
                message_text = f"Ohh No!! slave [{character_name}] Has Been Ran Away From Your Chat Store His/Her Name For Next Time"
                await context.bot.send_message(chat_id=chat_id, text=message_text)           
            if chat_id in ran_away_count:
                del ran_away_count[chat_id]
            del last_characters[chat_id]
warned_users = {}
async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    if user is None or user.is_bot:
        return  # Skip if the effective user is None or a bot
    user_id = user.id
    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]
    async with lock:

        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        if chat_frequency:
            message_frequency = chat_frequency.get('message_frequency', 100)
        else:
            message_frequency = 100

        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 10:
            
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return
                else:

                    await update.message.reply_text(f"⛔️ Flooding | Spamming\nNow I'm ⚠️ Ignoring {user.first_name} Existence For Upcoming 10 Minutes.")
                    warned_users[user_id] = time.time()
                    return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

        if chat_id in message_counts:
            message_counts[chat_id] += 1
        else:
            message_counts[chat_id] = 1

        if message_counts[chat_id] % message_frequency == 0:
            await send_image(update, context)
            message_counts[chat_id] = 0

async def set_rarity_percentages(chat_id, percentages):
    group_rarity_percentages[chat_id] = percentages


rarity_active = {
    "🔵 𝙇𝙊𝙒": True,
    "🟢 𝙈𝙀𝘿𝙄𝙐𝙈": True,
    "🔴 𝙃𝙄𝙂𝙃": True,
    "🟡 𝙉𝙊𝘽𝙀𝙇": True,
    "🥵 𝙉𝙐𝘿𝙀𝙎": True,
    "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿": True,
    "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]": True,
    "⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚": True,
    "🎭 𝙀𝙍𝙊𝙏𝙄𝘾": True,
    "🍑 𝙎𝙪𝙡𝙩𝙧𝙮": True
}
# Map numbers to rarity strings
rarity_map = {
    1: "🔵 𝙇𝙊𝙒",
    2: "🟢 𝙈𝙀𝘿𝙄𝙐𝙈",
    3: "🔴 𝙃𝙄𝙂𝙃",
    4: "🟡 𝙉𝙊𝘽𝙀𝙇",
    5: "🥵 𝙉𝙐𝘿𝙀𝙎",
    6: "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿",
    7: "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]",
    8: "⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚",
    9: "🎭 𝙀𝙍𝙊𝙏𝙄𝘾",
    10: "🍑 𝙎𝙪𝙡𝙩𝙧𝙮"
}
# Command to turn a rarity on
async def set_on(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != 7011990425:
        await update.message.reply_text("only Ram can use this command.")
        return
    try:
        rarity_number = int(context.args[0])
        rarity = rarity_map.get(rarity_number)
        if rarity and rarity in rarity_active:
            if not rarity_active[rarity]:
                rarity_active[rarity] = True
                await update.message.reply_text(f'Rarity {rarity} is now ON and will spawn from now on.')
            else:
                await update.message.reply_text(f'Rarity {rarity} is already ON.')
        else:
            await update.message.reply_text('Invalid rarity number.')
    except (IndexError, ValueError):
        await update.message.reply_text('Please provide a valid rarity number.')
# Command to turn a rarity off
async def set_off(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != 7011990425:
        await update.message.reply_text("Only Ram Can use this command.")
        return
    try:
        rarity_number = int(context.args[0])
        rarity = rarity_map.get(rarity_number)
        if rarity and rarity in rarity_active:
            if rarity_active[rarity]:
                rarity_active[rarity] = False
                await update.message.reply_text(f'Rarity {rarity} is now OFF and will not spawn from now on.')
            else:
                await update.message.reply_text(f'Rarity {rarity} is already OFF.')
        else:
            await update.message.reply_text('Invalid rarity number.')
    except (IndexError, ValueError):
        await update.message.reply_text('Please provide a valid rarity number.')

async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    all_characters = list(await collection.find({}).to_list(length=None))

    if chat_id not in sent_characters:
        sent_characters[chat_id] = []
    
    if len(sent_characters[chat_id]) == len(all_characters):
        sent_characters[chat_id] = []

    # Set rarity percentages based on chat ID
    if chat_id == -1002041586214:
        rarity_percentages = {
            "🔵 𝙇𝙊𝙒": 50,
            "🟢 𝙈𝙀𝘿𝙄𝙐𝙈": 40,
            "🔴 𝙃𝙄𝙂𝙃": 30,
            "🟡 𝙉𝙊𝘽𝙀𝙇": 40,
            "🥵 𝙉𝙐𝘿𝙀𝙎": 0.1,
            "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿": 0.1,
            "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]": 0.1,
            "⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚": 10,
            "🎭 𝙀𝙍𝙊𝙏𝙄𝘾": 0.1,
            "🍑 𝙎𝙪𝙡𝙩𝙧𝙮": 0
        }
    else:
        rarity_percentages = {
            "🔵 𝙇𝙊𝙒": 50,
            "🟢 𝙈𝙀𝘿𝙄𝙐𝙈": 40,
            "🔴 𝙃𝙄𝙂𝙃": 30,
            "🟡 𝙉𝙊𝘽𝙀𝙇": 1,
            "🥵 𝙉𝙐𝘿𝙀𝙎": 0,
            "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿": 0,
            "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]": 0,
            "⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚": 1,
            "🎭 𝙀𝙍𝙊𝙏𝙄𝘾": 0,
            "🍑 𝙎𝙪𝙡𝙩𝙧𝙮": 0
        }

    multiplier = 100
    weighted_characters = [
        c for c in all_characters if 'rarity' in c and rarity_active.get(c['rarity'], False)
        for _ in range(int(multiplier * rarity_percentages.get(c['rarity'], 0)))
    ]

    if not weighted_characters:
        await update.message.reply_text('No active characters available to send.')
        return

    character = random.choice(weighted_characters)
    sent_characters[chat_id].append(character['id'])
    last_characters[chat_id] = character

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=character['img_url'],
        caption=f"""ᴀ ɴᴇᴡ ( {character['rarity']} ) ꜱʟᴀᴠᴇ ʜᴀꜱ ᴀᴘᴘᴇᴀʀᴇᴅ!\nᴜsᴇ /slave [ɴᴀᴍᴇ] ᴀɴᴅ ᴀᴅᴅ ɪɴ ʏᴏᴜʀ ʜᴀʀᴇᴍ!""",
        parse_mode='Markdown'
    )

async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if chat_id not in last_characters:
        return
    if chat_id in first_correct_guesses:
        await update.message.reply_text(f'❌ 𝘼𝙡𝙧𝙚𝙖𝙙𝙮 𝘽𝙚𝙘𝙤𝙢𝙚 𝙎𝙤𝙢𝙚𝙤𝙣𝙚 𝙎𝙇𝘼𝙑𝙀..')
        return
    guess = ' '.join(context.args).lower() if context.args else ''
    if "()" in guess or "&" in guess.lower():
        await update.message.reply_text("𝙉𝙖𝙝𝙝 𝙔𝙤𝙪 𝘾𝙖𝙣'𝙩 𝙪𝙨𝙚 𝙏𝙝𝙞𝙨 𝙏𝙮𝙥𝙚𝙨 𝙤𝙛 𝙬𝙤𝙧𝙙𝙨 ❌️")
        return
    name_parts = last_characters[chat_id]['name'].lower().split()
    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
        first_correct_guesses[chat_id] = user_id
        user = await user_collection.find_one({'id': user_id})
        if user:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != user.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != user.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': last_characters[chat_id]}})
        elif hasattr(update.effective_user, 'username'):
            await user_collection.insert_one({
                'id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'characters': [last_characters[chat_id]],
            })
        group_user_total = await group_user_totals_collection.find_one({'user_id': user_id, 'group_id': chat_id})
        if group_user_total:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != group_user_total.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != group_user_total.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$set': update_fields})
            await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$inc': {'count': 1}})
        else:
            await group_user_totals_collection.insert_one({
                'user_id': user_id,
                'group_id': chat_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'count': 1,
            })
        group_info = await top_global_groups_collection.find_one({'group_id': chat_id})
        if group_info:
            update_fields = {}
            if update.effective_chat.title != group_info.get('group_name'):
                update_fields['group_name'] = update.effective_chat.title
            if update_fields:
                await top_global_groups_collection.update_one({'group_id': chat_id}, {'$set': update_fields})
            await top_global_groups_collection.update_one({'group_id': chat_id}, {'$inc': {'count': 1}})
        else:
            await top_global_groups_collection.insert_one({
                'group_id': chat_id,
                'group_name': update.effective_chat.title,
                'count': 1,
            })
        keyboard = [[InlineKeyboardButton(f"𝙎𝙇𝘼𝙑𝙀𝙎 🔥", switch_inline_query_current_chat=f"collection.{user_id}")]]
        await update.message.reply_text(f'<b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b> 𝙔𝙤𝙪 𝙂𝙤𝙩 𝙉𝙚𝙬 𝙎𝙇𝘼𝙑𝙀🫧 \n🌸𝗡𝗔𝗠𝗘: <b>{last_characters[chat_id]["name"]}</b> \n🖼𝗔𝗡𝗜𝗠𝗘: <b>{last_characters[chat_id]["anime"]}</b> \n𝙍𝘼𝙍𝙄𝙏𝙔: <b>{last_characters[chat_id]["rarity"]}</b>\n\n⛩ 𝘾𝙝𝙚𝙘𝙠 𝙮𝙤𝙪𝙧 /slaves 𝙉𝙤𝙬', parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text('𝙋𝙡𝙚𝙖𝙨𝙚 𝙒𝙧𝙞𝙩𝙚 𝘾𝙤𝙧𝙧𝙚𝙘𝙩 𝙉𝙖𝙢𝙚... ❌️')
def main() -> None:
    """Run bot."""
    application.add_handler(CommandHandler(["slave"], guess, block=False))
    application.add_handler(CommandHandler('set_on', set_on, block=False))
    application.add_handler(CommandHandler('set_off', set_off, block=False))
    application.add_handler(MessageHandler(filters.ALL, message_counter, block=False))
    PORT = int(os.environ.get("PORT", "8443"))
    TOKEN = os.environ.get("TOKEN")
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if not TOKEN or not RENDER_EXTERNAL_URL:
        LOGGER.error("Environment variables TOKEN or RENDER_EXTERNAL_URL are not set")
        return
    # Set the webhook URL
    WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}/{TOKEN}"
    # Log the values for debugging
    LOGGER.info(f"PORT: {PORT}")
    LOGGER.info(f"TOKEN: {TOKEN}")
    LOGGER.info(f"RENDER_EXTERNAL_URL: {RENDER_EXTERNAL_URL}")
    LOGGER.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
    # Start webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )
if __name__ == "__main__":
    shivuu.start()
    LOGGER.info("Bot started")
    main()
