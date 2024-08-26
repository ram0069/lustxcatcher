from pyrogram import Client, filters
from shivu import user_collection, collection
from shivu import shivuu as bot

@bot.on_message(filters.command(["solve"]))
async def update_names(client, message):
    # Check if the user is authorized
    if message.from_user.id == 7011990425:
        print("Starting the update process...")

        try:
            async for user in user_collection.find():
                updated_characters = []

                # Iterate over each character and update the name
                for character in user['characters']:
                    # Fetch the original character from the same collection
                    original_character = await collection.find_one({'id': character['id']})
                    if original_character:
                        original_name = original_character['name']
                    else:
                        original_name = character['name']  # Fallback to current name if not found

                    updated_characters.append({
                        'id': character['id'],
                        'name': original_name,  # Update with the original name
                        'anime': character['anime'],
                        'img_url': character['img_url'],
                        'rarity': character['rarity'],
                        'count': character.get('count', 1)  # Preserve original count or set to 1 if not present
                    })

                # Update the user's characters in the database
                result = await user_collection.update_one(
                    {'id': user['id']},  # Ensure you're using the correct identifier
                    {'$set': {'characters': updated_characters}}
                )

                if result.modified_count == 1:
                    print(f"Names updated successfully for user: {user['id']}")
                else:
                    print(f"Name update failed for user: {user['id']}")
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        await message.reply("You are not authorized to use this command.")
