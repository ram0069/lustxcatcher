from telegram.ext import CommandHandler
from random import choices
from shivu import application, user_collection, collection

# Replace OWNER_ID with the actual owner's user ID
OWNER_ID = 7011990425

# Rarity percentages
rarity_percentages = {
    "🔵 𝙇𝙊𝙒": 0,
    "🟢 𝙈𝙀𝘿𝙄𝙐𝙈": 0,
    "🔴 𝙃𝙄𝙂𝙃": 0,
    "🟡 𝙉𝙊𝘽𝙀𝙇": 0,
    "🥵 𝙉𝙐𝘿𝙀𝙎": 100,
    "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿": 0,
    "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]": 0,
    "⚫️ [𝙓] 𝙑𝙚𝙧𝙨𝙚": 0,
    "🎭 𝙀𝙍𝙊𝙏𝙄𝘾": 0,
    "🍑 𝙎𝙪𝙡𝙩𝙧𝙮": 0
}

async def giverandom(update, context):
    try:
        # Check if the user is the owner
        user_id = update.effective_user.id
        if user_id != OWNER_ID:
            await update.message.reply_text('You are not authorized to use this command.')
            return

        # Ensure the command has the correct number of arguments
        if len(context.args) != 2:
            await update.message.reply_text('Please provide a valid user ID and the number of waifus to give.')
            return

        try:
            receiver_id = int(context.args[0])
            waifu_count = int(context.args[1])
        except ValueError:
            await update.message.reply_text('Invalid user ID or waifu count provided.')
            return

        # Retrieve the receiver's information
        receiver = await user_collection.find_one({'id': receiver_id})

        # Check if the receiver exists
        if not receiver:
            await update.message.reply_text(f'Receiver with ID {receiver_id} not found.')
            return

        # Get a list of random waifus from the collection
        all_waifus = await collection.find({}).to_list(None)
        valid_waifus = [waifu for waifu in all_waifus if 'rarity' in waifu]
        waifu_weights = [rarity_percentages.get(waifu['rarity'], 0) for waifu in valid_waifus]
        random_waifus = choices(valid_waifus, weights=waifu_weights, k=waifu_count)

        # Add the random waifus to the receiver's waifu collection
        receiver_waifus = receiver.get('characters', [])
        receiver_waifus.extend(random_waifus)

        # Update the receiver's waifus
        await user_collection.update_one({'id': receiver_id}, {'$set': {'characters': receiver_waifus}})

        await update.message.reply_text(f'Successfully gave {waifu_count} random waifus to user {receiver_id}!')

    except Exception as e:
        await update.message.reply_text(f'An error occurred: {e}')

# Register the giverandom command handler
application.add_handler(CommandHandler("giver", giverandom))
