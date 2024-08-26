import urllib.request
from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu.modules.database.sudo import is_user_sudo
from shivu import application, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

WRONG_FORMAT_TEXT = """Wrong ❌️ format...  eg. /upload Img_url muzan-kibutsuji Demon-slayer 3
img_url character-name anime-name rarity-number
use rarity number accordingly rarity Map
rarity_map =  1:🔵 𝙇𝙊𝙒, 2:🟢 𝙈𝙀𝘿𝙄𝙐𝙈, 3:🔴 𝙃𝙄𝙂𝙃, 4:🟡 𝙉𝙊𝘽𝙀L, 5:🥵 𝙉𝙐𝘿𝙀𝙎, 6:🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿, 7:💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇], 8:⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚, 9:🎭 𝙀𝙍𝙊𝙏𝙄𝘾, 10:🍑 𝙎𝙪𝙡𝙩𝙧𝙮"""

async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name}, 
        {'$inc': {'sequence_value': 1}}, 
        return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']
    
async def get_available_id():
    deleted_ids_collection = db.deleted_ids
    deleted_id_doc = await deleted_ids_collection.find_one_and_delete({})
    if deleted_id_doc:
        return deleted_id_doc['id']
    return str(await get_next_sequence_number('character_id')).zfill(2)
    
async def upload(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not await is_user_sudo(user_id):
        await update.message.reply_text('Ask Ram...')
        return

    args = context.args
    if len(args) != 4:
        await update.message.reply_text(WRONG_FORMAT_TEXT)
        return

    character_name = args[1].replace('-', ' ').title()
    anime = args[2].replace('-', ' ').title()

    try:
        urllib.request.urlopen(args[0])
    except:
        await update.message.reply_text('Invalid URL.')
        return

    rarity_map = {
        1: "🔵 𝙇𝙊𝙒", 2: "🟢 𝙈𝙀𝘿𝙄𝙐𝙈", 3: "🔴 𝙃𝙄𝙂𝙃", 4: "🟡 𝙉𝙊𝘽𝙀𝙇",
        5: "🥵 𝙉𝙐𝘿𝙀𝙎", 6: "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿", 7: "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]",
        8: "⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚", 9: "🎭 𝙀𝙍𝙊𝙏𝙄𝘾", 10: "🍑 𝙎𝙪𝙡𝙩𝙧𝙮"
    }

    try:
        rarity = rarity_map[int(args[3])]
    except KeyError:
        await update.message.reply_text('Invalid rarity. Please use 1, 2, 3, 4, 5, 6, 7, 8, 9, or 10.')
        return

    character_id = await get_available_id()
    character = {
        'img_url': args[0],
        'name': character_name,
        'anime': anime,
        'rarity': rarity,
        'id': character_id
    }

    try:
        message = await context.bot.send_photo(
            chat_id=CHARA_CHANNEL_ID,
            photo=args[0],
            caption=f'<b>Character Name:</b> {character_name}\n<b>Anime Name:</b> {anime}\n<b>Rarity:</b> {rarity}\n<b>ID:</b> {character_id}\nAdded by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>',
            parse_mode='HTML'
        )
        character['message_id'] = message.message_id
        await collection.insert_one(character)
        await update.message.reply_text('Character added successfully!')
    except Exception as e:
        await collection.insert_one(character)
        await update.message.reply_text(f'Character added, but there was an issue with the channel. Error: {str(e)}\nIf you think this is a source error, forward to: {SUPPORT_CHAT}')
        
async def delete(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not await is_user_sudo(user_id):
        await update.message.reply_text('Ask My Owner...')
        return

    args = context.args
    if len(args) != 1:
        await update.message.reply_text('Incorrect format. Please use: /delete ID')
        return

    character_id = args[0]
    character = await collection.find_one_and_delete({'id': character_id})

    if character:
        try:
            await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=character['message_id'])
            await db.deleted_ids.insert_one({'id': character_id})
            await update.message.reply_text('Character deleted successfully.')
        except Exception as e:
            await update.message.reply_text(f'Deleted from database, but there was an issue with the channel. Error: {str(e)}')
    else:
        await update.message.reply_text('Character not found in the database.')

async def update(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not await is_user_sudo(user_id):
        await update.message.reply_text('Ask My Owner...')
        return

    args = context.args
    if len(args) != 3:
        await update.message.reply_text('Incorrect format. Please use: /update id field new_value')
        return

    character_id = args[0]
    field = args[1]
    new_value = args[2]

    character = await collection.find_one({'id': character_id})
    if not character:
        await update.message.reply_text('Character not found.')
        return

    valid_fields = ['img_url', 'name', 'anime', 'rarity']
    if field not in valid_fields:
        await update.message.reply_text(f'Invalid field. Please use one of the following: {", ".join(valid_fields)}')
        return

    if field in ['name', 'anime']:
        new_value = new_value.replace('-', ' ').title()
    elif field == 'rarity':
        rarity_map = {
            1: "🔵 𝙇𝙊𝙒", 2: "🟢 𝙈𝙀𝘿𝙄𝙐𝙈", 3: "🔴 𝙃𝙄𝙂𝙃", 4: "🟡 𝙉𝙊𝘽𝙀𝙇",
            5: "🥵 𝙉𝙐𝘿𝙀𝙎", 6: "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿", 7: "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]",
            8: "⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚", 9: "🎭 𝙀𝙍𝙊𝙏𝙄𝘾", 10: "🍑 𝙎𝙪𝙡𝙩𝙧𝙮"
        }
        try:
            new_value = rarity_map[int(new_value)]
        except KeyError:
            await update.message.reply_text('Invalid rarity. Please use 1, 2, 3, 4, 5, 6, 7, 8, 9, or 10.')
            return

    await collection.find_one_and_update({'id': character_id}, {'$set': {field: new_value}})

    try:
        if field == 'img_url':
            await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=character['message_id'])
            message = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=new_value,
                caption=f'<b>Character Name:</b> {character["name"]}\n<b>Anime Name:</b> {character["anime"]}\n<b>Rarity:</b> {character["rarity"]}\n<b>ID:</b> {character["id"]}\nUpdated by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>',
                parse_mode='HTML'
            )
            character['message_id'] = message.message_id
            await collection.find_one_and_update({'id': character_id}, {'$set': {'message_id': message.message_id}})
        else:
            await context.bot.edit_message_caption(
                chat_id=CHARA_CHANNEL_ID,
                message_id=character['message_id'],
                caption=f'<b>Character Name:</b> {character["name"]}\n<b>Anime Name:</b> {character["anime"]}\n<b>Rarity:</b> {character["rarity"]}\n<b>ID:</b> {character["id"]}\nUpdated by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>',
                parse_mode='HTML'
            )

        await update.message.reply_text('Character updated successfully!')
    except Exception as e:
        await update.message.reply_text(f'Update successful, but there was an issue with the channel. Error: {str(e)}')

UPLOAD_HANDLER = CommandHandler('upload', upload, block=False)
application.add_handler(UPLOAD_HANDLER)
DELETE_HANDLER = CommandHandler('delete', delete, block=False)
application.add_handler(DELETE_HANDLER)
UPDATE_HANDLER = CommandHandler('update', update, block=False)
application.add_handler(UPDATE_HANDLER)
