from pyrogram import Client, filters
from shivu import db, collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection
import asyncio
from shivu import user_collection, collection, application
from shivu import sudo_users
from shivu import shivuu as app
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from shivu.modules.database.sudo import is_user_sudo
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler

async def give_character(receiver_id, character_id):
    character = await collection.find_one({'id': character_id})

    if character:
        try:
            await user_collection.update_one(
                {'id': receiver_id},
                {'$push': {'characters': character}}
            )

            img_url = character['img_url']
            caption = (
                f"🍀 Slave Added {receiver_id}\n"
                f"\n"
                f"🍥 Name : {character['name']}\n"
                f" Rarity : {character['rarity']}\n"
                f"🆔 ID : {character['id']}"
            )

            return img_url, caption
        except Exception as e:
            print(f"Error updating user: {e}")
            raise
    else:
        raise ValueError("Character not found.")

# Command to give a character, restricted to sudo users
async def give_character_command(update: Update, context: CallbackContext):
    message = update.message
    sender_id = message.from_user.id

    # Check if the user is a sudo user
    if not await is_user_sudo(sender_id):
        await message.reply_text("You are not authorized to use this command.")
        return

    # Check if a message is replied to
    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to give a character!")
        return

    try:
        # Split the message to get the character ID
        character_id = str(message.text.split()[1])
        receiver_id = message.reply_to_message.from_user.id

        # Call the function to give the character
        result = await give_character(receiver_id, character_id)

        if result:
            # If successful, send the photo and caption
            img_url, caption = result
            await message.reply_photo(photo=img_url, caption=caption)

    # Catch specific exceptions and provide appropriate messages
    except IndexError:
        await message.reply_text("Please provide a character ID.")
    except ValueError as e:
        await message.reply_text(str(e))  # Specific error message from the function
    except Exception as e:
        print(f"Error in give_character_command: {e}")
        await message.reply_text("An error occurred while processing the command.")

# Add command handler for /give command
application.add_handler(CommandHandler("give", give_character_command))
