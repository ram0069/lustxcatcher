import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import DESCENDING
import asyncio
import logging
from telegram import Update, InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import InlineQueryHandler, CallbackContext, ApplicationBuilder, CallbackQueryHandler, CommandHandler
from shivu import user_collection, collection, application, db

lock = asyncio.Lock()
# Ensure indexes are created for faster lookups
db.characters.create_index([('id', DESCENDING)])
db.characters.create_index([('anime', DESCENDING)])
db.characters.create_index([('img_url', DESCENDING)])
db.user_collection.create_index([('characters.id', DESCENDING)])
db.user_collection.create_index([('characters.name', DESCENDING)])
db.user_collection.create_index([('characters.img_url', DESCENDING)])
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=600)
# Function to clear the caches
def clear_all_caches():
    all_characters_cache.clear()
    user_collection_cache.clear()
# Call the function to clear the caches
clear_all_caches()
async def fetch_characters_from_db(query_regex=None):
    if query_regex:
        characters = await collection.find({"$or": [{"name": query_regex}, {"anime": query_regex}]}, {'name': 1, 'anime': 1, 'img_url': 1, 'rarity': 1, 'id': 1}).to_list(length=None)
    else:
        characters = await collection.find({}, {'name': 1, 'anime': 1, 'img_url': 1, 'rarity': 1, 'id': 1}).to_list(length=None)
    return characters
async def fetch_user_from_db(user_id):
    return await user_collection.find_one({'id': int(user_id)}, {'characters': 1, 'id': 1, 'first_name': 1})
async def inlinequery(update: Update, context: CallbackContext) -> None:
    async with lock:
        query = update.inline_query.query
        offset = int(update.inline_query.offset) if update.inline_query.offset else 0
        results_per_page = 30 
        start_index = offset
        end_index = offset + results_per_page
        all_characters = []
        user = None
        if query.startswith('collection.'):
            user_id, *search_terms = query.split(' ')[0].split('.')[1], ' '.join(query.split(' ')[1:])
            if user_id.isdigit():
                if user_id in user_collection_cache:
                    user = user_collection_cache[user_id]
                else:
                    user = await fetch_user_from_db(user_id)
                    user_collection_cache[user_id] = user
                if user:
                    all_characters = [v for v in user['characters'] if isinstance(v, dict) and 'id' in v]
                    if search_terms:
                        regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                        all_characters = [character for character in all_characters if regex.search(character['name']) or regex.search(character['anime'])]
            else:
                all_characters = []
                logging.warning(f"Invalid user_id format: {user_id}")
        else:
            if query:
                regex = re.compile(query, re.IGNORECASE)
                all_characters = await fetch_characters_from_db(regex)
            else:
                if 'all_characters' in all_characters_cache:
                    all_characters = all_characters_cache['all_characters']
                else:
                    all_characters = await fetch_characters_from_db()
                    all_characters_cache['all_characters'] = all_characters
        # Ensure no duplicate characters in the results
        unique_characters = {char['id']: char for char in all_characters if isinstance(char, dict) and 'id' in char}.values()
        # Slice the characters based on the current offset and results per page
        characters = list(unique_characters)[start_index:end_index]
        # Calculate the next offset
        next_offset = str(end_index) if len(characters) == results_per_page else ""
        results = []
        for character in characters:
            global_count = await user_collection.count_documents({'characters.id': character['id']})
            anime_characters = await collection.count_documents({'anime': character['anime']})
            if query.startswith('collection.'):
                user_character_count = sum(1 for c in user['characters'] if isinstance(c, dict) and c.get('id') == character.get('id'))
                user_anime_characters = sum(1 for c in user['characters'] if isinstance(c, dict) and c.get('anime') == character.get('anime'))
                caption = (
                    f"<b>OwO! Check out <a href='tg://user?id={user['id']}'>{escape(user.get('first_name', user['id']))}</a>'s Slave</b>\n\n"
                    f"{character['id']}: <b>{character['name']} (x{user_character_count})</b>\n"
                    f"<b>{character['anime']} ({user_anime_characters}/{anime_characters})</b>\n"
                    f"<b>(𝙍𝘼𝙍𝙄𝙏𝙔: {character['rarity']})</b>"
                )
                # Check for tags in character's name
                if '🐰' in character['name']:
                    caption += "\n\n🐰 𝓑𝓾𝓷𝓷𝔂 🐰"
                elif '👩‍🏫' in character['name']:
                    caption += "\n\n👩‍🏫 𝓣𝓮𝓪𝓬𝓱𝓮𝓻 👩‍🏫"
                elif '🎒' in character['name']:
                    caption += "\n\n🎒 𝓢𝓬𝓱𝓸𝓸𝓵 🎒"
                elif '👘' in character['name']:
                    caption += "\n\n👘 𝓚𝓲𝓶𝓸𝓷𝓸 👘"
                elif '🏖' in character['name']:
                    caption += "\n\n🏖 𝓢𝓤𝓜𝓜𝓔𝓡 🏖"
            else:
                caption = (
                    f"<b>OwO! Check out this Slave !!</b>\n\n"
                    f"{character['id']}: <b>{character['name']}</b>\n"
                    f"<b>{character['anime']}</b>\n"
                    f"<b>(𝙍𝘼𝙍𝙄𝙏𝙔: {character['rarity']})</b>\n"
                )
                # Check for tags in character's name
                if '🐰' in character['name']:
                    caption += "\n🐰 𝓑𝓾𝓷𝓷𝔂 🐰\n"
                elif '👩‍🏫' in character['name']:
                    caption += "\n👩‍🏫 𝓣𝓮𝓪𝓬𝓱𝓮𝓻 👩‍🏫\n"
                elif '🎒' in character['name']:
                    caption += "\n🎒 𝓢𝓬𝓱𝓸𝓸𝓵 🎒\n"
                elif '👘' in character['name']:
                    caption += "\n👘 𝓚𝓲𝓶𝓸𝓷𝓸 👘\n"
                elif '🏖' in character['name']:
                    caption += "\n\n🏖 𝓢𝓤𝓜𝓜𝓔𝓡 🏖\n"
            results.append(
                InlineQueryResultPhoto(
                    thumbnail_url=character['img_url'],
                    id=f"{character['id']}_{time.time()}",
                    photo_url=character['img_url'],
                    caption=caption,
                    parse_mode='HTML',
                    photo_width=300,  # Adjust the width as needed
                    photo_height=300,  # Adjust the height as neede
                )
            )
        # Add a fallback result if no characters are found
        if not results:
            results.append(
                InlineQueryResultArticle(
                    id='no_results',
                    title="No Slave Found",
                    input_message_content=InputTextMessageContent("No Slave Found"),
                    description="No matching Slave were found."
                )
            )
        await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)
application.add_handler(InlineQueryHandler(inlinequery, block=False))
