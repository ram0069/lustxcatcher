from pymongo import TEXT
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, collection

async def find(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /find name')
            return

        search_query = args[0].replace('-', ' ').title()

        # Perform case-insensitive partial match search using text index
        cursor = collection.find({'$text': {'$search': search_query}})

        found_characters = await cursor.to_list(None)

        if found_characters:
            # Extract the IDs from found characters and wrap each in <code> tags
            ids_list = [f'<code>{char["id"]}</code>' for char in found_characters]
            ids_text = ', '.join(ids_list)
            await update.message.reply_text(f"IDs of found slave: {ids_text}", parse_mode='HTML')
        else:
            await update.message.reply_text('No slave found.')

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

FIND_HANDLER = CommandHandler('find', find, block=False)
application.add_handler(FIND_HANDLER)

# Create a text index on the 'name' field
collection.create_index([('name', TEXT)], default_language='english')
