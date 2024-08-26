from telegram.ext import CommandHandler
from shivu import collection, user_collection, application, db, CHARA_CHANNEL_ID

async def sell(update, context):
    user_id = update.effective_user.id

    # Check if the command includes a character ID
    if not context.args or len(context.args) != 1:
        await update.message.reply_text('Please provide a valid Character ID to sell.')
        return
    character_id = context.args[0]
    # Retrieve the character from the harem based on the provided ID
    character = await collection.find_one({'id': character_id})
    if not character:
        await update.message.reply_text('Slave Not Found.')
        return
    # Check if the user has the character in their harem
    user = await user_collection.find_one({'id': user_id})
    if not user or 'characters' not in user:
        await update.message.reply_text('You do not own this slave in your harem.')
        return
    # Check if the character is present in the user's harem and get its count
    character_count = sum(1 for char in user.get('characters', []) if char['id'] == character_id)
    if character_count == 0:
        await update.message.reply_text('You do not own this slave in your harem.')
        return

    # Determine the coin value based on the rarity of the character
    rarity_coin_mapping = {
        "🔵 𝙇𝙊𝙒": 2000,
        "🟢 𝙈𝙀𝘿𝙄𝙐𝙈": 4000,
        "🔴 𝙃𝙄𝙂𝙃": 5000,
        "🟡 𝙉𝙊𝘽𝙀𝙇": 10000,
        "🥵 𝙉𝙐𝘿𝙀𝙎": 30000,
        "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿": 20000,
        "💋 𝘾𝙊𝙎𝙋𝙇𝘼𝙔 [𝙇]": 40000,
    }

    rarity = character.get('rarity', 'Unknown Rarity')
    coin_value = rarity_coin_mapping.get(rarity, 0)

    if coin_value == 0:
        await update.message.reply_text('Invalid rarity. Cannot determine the coin value.')
        return

    # Find the specific character instance to sell (only the first one)
    character_to_sell = next((char for char in user.get('characters', []) if char['id'] == character_id), None)
    if character_to_sell:
        # Remove the sold character from the user's harem
        await user_collection.update_one(
            {'id': user_id},
            {'$pull': {'characters': {'id': character_id}}, '$inc': {'count': -1}}
        )

        # Add coins to the user's balance
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': coin_value}})
        await update.message.reply_photo(
            photo=character['img_url'],
            caption=f"𝙎𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮 𝙎𝙤𝙡𝙙 𝙎𝙡𝙖𝙫𝙚 🌸\n𝙎𝙡𝙖𝙫𝙚 𝙉𝙖𝙢𝙚⚡️  : {character_to_sell['name']}\n𝙎𝙡𝙤𝙙 𝙁𝙤𝙧 : {coin_value}💸 𝙏𝙤𝙠𝙚𝙣𝙨."
        )
    else:
        await update.message.reply_text("You do not own this specific instance of the slave in your harem.")

sell_handler = CommandHandler("sell", sell, block=False)
application.add_handler(sell_handler)
