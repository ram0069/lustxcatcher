import random
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection  # Make sure to import the user_collection
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from pyrogram.types import Message  
from datetime import datetime, timedelta
from shivu import application
from html import escape

beast_list = {
    1: {'name': '𝐋𝐮𝐜𝐲', 'price': 5000000, 'rarity': '🐱 𝐂𝐚𝐭', 'power': 500, 'img_url': 'https://te.legra.ph/file/da3a63b484c2be011d85a.jpg'},
    2: {'name': '𝐌𝐨𝐥𝐥𝐲', 'price': 1000000, 'rarity': '🐮 𝐂𝐨𝐰', 'power': 1000, 'img_url': 'https://te.legra.ph/file/a38d89fc6eb6b67066ea4.jpg'},
    3: {'name': '𝐂𝐡𝐥𝐨𝐞', 'price': 7500000, 'rarity': '🦊 𝐅𝐨𝐱', 'power': 2000, 'img_url': 'https://te.legra.ph/file/359b56d65666f21f2eabf.jpg'},
    4: {'name': '𝐊𝐢𝐫𝐛𝐲', 'price': 10000000, 'rarity': '🐰 𝐁𝐮𝐧𝐧𝐲', 'power': 1000, 'img_url': 'https://te.legra.ph/file/90ceb0a1306a8ee34cf7f.png'},
    5: {'name': '𝐒𝐢𝐨𝐧𝐢𝐚', 'price': 50000000, 'rarity': '🌱 𝐄𝐥𝐟', 'power': 50000, 'img_url': 'https://te.legra.ph/file/57efcb1f726ef5b97c27b.jpg'},
    6: {'name': '𝐅𝐫𝐞𝐝𝐚', 'price': 75000000, 'rarity': '🍑 𝐒𝐮𝐜𝐂𝐮𝐜𝐮𝐬', 'power': 100000, 'img_url': 'https://te.legra.ph/file/221a012bac35527c81924.png'},
    7: {'name': '𝐂𝐚𝐥𝐚𝐭𝐡𝐢𝐞𝐥', 'price': 100000000, 'rarity': '🐉 𝐃𝐫𝐚𝐠𝐨𝐧', 'power': 200000, 'img_url': 'https://te.legra.ph/file/471cb23e1dffd9bd11137.jpg'},
    8: {'name': '𝐆𝐞𝐧𝐞𝐯𝐚', 'price': 250000, 'rarity': '🍃 𝐆𝐨𝐛𝐥𝐢𝐧', 'power': 1000, 'img_url': 'https://te.legra.ph/file/e8fd10072222ee8a8a088.png'},
    9: {'name': '𝐇𝐚𝐳𝐞𝐥', 'price': 60000000, 'rarity': '🍁 𝐎𝐧𝐢', 'power': 15000, 'img_url': 'https://te.legra.ph/file/87ba232e727d802ebe69b.png'},
    10: {'name': '𝐂𝐨𝐫𝐚𝐥', 'price': 40000000, 'rarity': '🌳 𝐖𝐨𝐫𝐥𝐝 𝐓𝐫𝐞𝐞', 'power': 30000, 'img_url': 'https://te.legra.ph/file/2974a9dc120a1239643a2.jpg'},
    11: {'name': '𝐁𝐫𝐢𝐚𝐫', 'price': 20000000, 'rarity': '🍂 𝐃𝐚𝐫𝐤 𝐄𝐥𝐟', 'power': 75000, 'img_url': 'https://te.legra.ph/file/1c902b35c6bc40658bd44.png'},
    12: {'name': '𝐀𝐮𝐫𝐞𝐥𝐢𝐚', 'price': 80000000, 'rarity': '👹 𝐃𝐞𝐦𝐨𝐧', 'power': 100000, 'img_url': 'https://te.legra.ph/file/1d7352c01ff9c0235e6ff.png'},
    13: {'name': '𝐀𝐭𝐥𝐚𝐧𝐭𝐚', 'price': 150000000, 'rarity': '🍑 𝐒𝐮𝐜𝐂𝐮𝐜𝐮𝐬', 'power': 150000, 'img_url': 'https://te.legra.ph/file/f32cefc258b5116283eef.png'},
    14: {'name': '𝐍𝐞𝐥𝐥𝐢𝐞', 'price': 200000000, 'rarity': '🪽 𝐀𝐧𝐠𝐞𝐥', 'power': 200000, 'img_url': 'https://te.legra.ph/file/23760a2dfdc9c99bda26f.png'},
}

async def get_user_data(user_id):
    return await user_collection.find_one({'id': user_id})

cooldowns = {}

@bot.on_message(filters.command(["beastshop"]))
async def beastshop_cmd(_: bot, update: t.Update):
    # Display a list of available beasts and their prices
    beast_list_text = "\n".join([f"{beast_id}. {beast['name']} - 𝐑𝐚𝐜𝐞 : {beast['rarity']}, 𝐏𝐫𝐢𝐜𝐞 : Ŧ`{beast['price']}`" for beast_id, beast in beast_list.items()])
    return await update.reply_text(f"⛩「𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐁𝐞𝐚𝐬𝐭 𝐬𝐡𝐨𝐩」🔞\n\n{beast_list_text}\n\nUse `/buybeast <beast_id>` to purchase a beast.")

@bot.on_message(filters.command(["buybeast"]))
async def buybeast_cmd(_: bot, update: t.Update):
    user_id = update.from_user.id
    user_data = await get_user_data(user_id)

    # Check if the user has already bought the specified beast
    beast_id = int(update.text.split()[1]) if len(update.text.split()) > 1 else None

    if beast_id is not None:
        beast_type = beast_list[beast_id]['name'].lower()
        if 'beasts' in user_data and any(beast['name'].lower() == beast_type for beast in user_data.get('beasts', [])):
            return await update.reply_text(f"You already own a {beast_type.capitalize()} beast. Choose a different type from /beastshop.")

    # Check if the specified beast_id is valid
    if beast_id not in beast_list:
        return await update.reply_text("Usage : `/buybeast 1/which one you want`.")

    # Check if the user has enough tokens to buy the beast
    beast_price = beast_list[beast_id]['price']
    if user_data.get('balance', 0) < beast_price:
        return await update.reply_text(f"You don't have enough tokens to buy this beast. You need {beast_price} tokens.")

    # Deduct the beast price from the user's balance
    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -beast_price}})

    # Add the new beast to the user's list of beasts with rarity information
    new_beast = {'id': beast_id, 'name': beast_list[beast_id]['name'], 'rarity': beast_list[beast_id]['rarity'], 'img_url': beast_list[beast_id]['img_url'], 'power': beast_list[beast_id]['power']}
    await user_collection.update_one({'id': user_id}, {'$push': {'beasts': new_beast}})

    return await update.reply_photo(photo=beast_list[beast_id]['img_url'], caption=f"You have successfully purchased a {beast_list[beast_id]['name']}! Use /beast to see your new beast.")

@bot.on_message(filters.command(["beast"]))
async def showbeast_cmd(_: bot, update: t.Update):
    user_id = update.from_user.id
    user_data = await get_user_data(user_id)

    # Check if the user has any beasts
    if 'beasts' in user_data and user_data['beasts']:
        # Check if the user has a main beast set
        main_beast_id = user_data.get('main_beast')

        # Generate text for other beasts
        other_beasts_text = "\n".join([f"𝐈𝐃 : {beast.get('id', 'N/A')} ⌠ {beast.get('rarity', 'N/A')} ⌡ {beast.get('name', 'N/A')} (𝐏𝐨𝐰𝐞𝐫: `{beast.get('power', 'N/A')}`)" for beast in user_data['beasts']])

        if main_beast_id:
            main_beast = next((beast for beast in user_data['beasts'] if beast['id'] == main_beast_id), None)
            if main_beast:
                await update.reply_photo(
                    photo=main_beast['img_url'],
                    caption="⛩️ 𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐭𝐡𝐞 𝐟𝐨𝐥𝐥𝐨𝐰𝐢𝐧𝐠 𝐛𝐞𝐚𝐬𝐭 𝐬𝐥𝐚𝐯𝐞 ⛩️\n\n" + other_beasts_text + "\n\n𝐔𝐬𝐞 /binfo <𝐢𝐝> 𝐭𝐨 𝐬𝐞𝐞 𝐲𝐨𝐮𝐫 𝐛𝐞𝐚𝐬𝐭",
                )
                return

        return await update.reply_text(other_beasts_text + "\n")
    
    return await update.reply_text("You don't have any beasts. Buy a beast using `/beastshop`.")
    
# Add a new command to show beast details along with an image
from pyrogram import filters
from pyrogram.types import Update
from html import escape

@bot.on_message(filters.command(["binfo"]))
async def showbeastdetails_cmd(_, update: Update):
    user_id, user_data = update.from_user.id, await get_user_data(update.from_user.id)

    if 'beasts' in user_data and user_data['beasts']:
        beast_id = int(update.text.split()[1]) if len(update.text.split()) > 1 else None

        if beast_id is not None:
            selected_beast = next((beast for beast in user_data.get('beasts', []) if beast.get('id') == beast_id), None)

            if selected_beast and all(key in selected_beast for key in ('img_url', 'name', 'rarity', 'power')):
                user_first_name = update.from_user.first_name
                user_link = f'<a href="tg://user?id={user_id}">{escape(user_first_name)}</a>'
                caption = (
                    f"𝐎𝐰𝐎! 𝐂𝐡𝐞𝐜𝐤 𝐨𝐮𝐭 𝐭𝐡𝐢𝐬 {user_link} 𝐁𝐞𝐚𝐬𝐭!\n\n"
                    f"🌸 𝐍𝐚𝐦𝐞: {selected_beast['name']}\n"
                    f"🧬 𝐁𝐞𝐚𝐬𝐭 𝐑𝐚𝐜𝐞: {selected_beast['rarity']}\n"
                    f"🔮 𝐏𝐨𝐰𝐞𝐫: `{selected_beast['power']}`\n"
                    f"(🆔 `{beast_id}`)\n\n"
                )
                await update.reply_photo(photo=selected_beast['img_url'], caption=caption)
                return
    
    await update.reply_text("You don't own that beast. Use `/binfo` to see your available beasts.")

@bot.on_message(filters.command(["givebeast"]) & filters.user(6890857225))
async def givebeast_cmd(_: bot, update: t.Update):
    try:
        # Extract user_id and beast_id from the command
        _, user_id, beast_id = update.text.split()
        user_id = int(user_id)
        beast_id = int(beast_id)

        # Check if the beast_id is valid
        if beast_id not in beast_list:
            return await update.reply_text("Invalid beast ID. Choose a valid beast ID.")

        # Check if the user exists
        user_data = await get_user_data(user_id)
        if not user_data:
            return await update.reply_text("User not found.")

        # Add the new beast to the user's list of beasts with rarity information
        new_beast = {'id': beast_id, 'name': beast_list[beast_id]['name'], 'rarity': beast_list[beast_id]['rarity'], 'img_url': beast_list[beast_id]['img_url'], 'power': beast_list[beast_id]['power']}
        await user_collection.update_one({'id': user_id}, {'$push': {'beasts': new_beast}})

        return await update.reply_text(f"Beast {beast_list[beast_id]['name']} has been successfully given to user {user_id}.")

    except ValueError:
        return await update.reply_text("Invalid command format. Use /givebeast <user_id> <beast_id>.")

# Command for the bot owner to delete all beasts of a user
@bot.on_message(filters.command(["delbeast"]) & filters.user(6890857225))
async def deletebeasts_cmd(_: bot, update: t.Update):
    try:
        # Extract user_id from the command
        _, user_id = update.text.split()
        user_id = int(user_id)

        # Check if the user exists
        user_data = await get_user_data(user_id)
        if not user_data:
            return await update.reply_text("User not found.")

        # Remove all beasts of the user
        await user_collection.update_one({'id': user_id}, {'$unset': {'beasts': 1}})

        return await update.reply_text(f"All beasts of user {user_id} have been deleted.")

    except ValueError:
        return await update.reply_text("Invalid command format. Use /delbeast <user_id>.")

@bot.on_message(filters.command(["setbeast"]))
async def setbeast_cmd(_: bot, update: t.Update):
    user_id = update.from_user.id
    user_data = await get_user_data(user_id)

    # Check if the user has any beasts
    if 'beasts' in user_data and user_data['beasts']:
        # Extract the beast ID from the command
        beast_id = int(update.text.split()[1]) if len(update.text.split()) > 1 else None

        if beast_id is not None:
            # Check if the specified beast_id exists in the user's collection
            if any(beast['id'] == beast_id for beast in user_data['beasts']):
                # Set the selected beast as the user's main beast
                await user_collection.update_one({'id': user_id}, {'$set': {'main_beast': beast_id}})
                return await update.reply_text("Your main beast has been set successfully.")
            else:
                return await update.reply_text("You don't own a beast with that ID.")
        else:
            return await update.reply_text("Invalid command format. Use `/setbeast 1/the one you want to set in mein`.")
    else:
        return await update.reply_text("You don't have any beasts. Buy a beast using `/beastshop`.")

@bot.on_message(filters.command(["btop"]))
async def top_beasts(_, message: Message):
    # Get the top 10 users with their respective number of beasts
    top_users = await user_collection.aggregate([
        {"$project": {"id": 1, "first_name": 1, "num_beasts": {"$size": {"$ifNull": ["$beasts", []]}}}},
        {"$sort": {"num_beasts": -1}},
        {"$limit": 10}
    ]).to_list(10)

    if top_users:
        response = "𝐓𝐨𝐩 𝟏𝟎 𝐔𝐬𝐞𝐫𝐬 𝐰𝐢𝐭𝐡 𝐌𝐨𝐬𝐭 𝐁𝐞𝐚𝐬𝐭'𝐬 :\n\n"
        for index, user_data in enumerate(top_users, start=1):
            first_name = user_data.get('first_name', 'N/A')
            num_beasts = user_data.get('num_beasts', 0)
            user_id = user_data.get('id')
            user_link = f'<a href="tg://user?id={user_id}">{escape(first_name)}</a>'
            response += f"({index}) {user_link} ➾ `{num_beasts}` beast's\n"

        # Select a random photo URL
        photo_urls = [
            "https://te.legra.ph/file/a316aae0cc355b3e6a1c4.png",
            # Add more photo URLs as needed
        ]
        random_photo_url = random.choice(photo_urls)

        # Reply with the leaderboard and the photo
        await message.reply_photo(photo=random_photo_url, caption=response)
    else:
        await message.reply_text("No users found.")
