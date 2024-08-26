from telegram.ext import CommandHandler
from shivu import application, user_collection

# Replace OWNER_ID with the actual owner's user ID
OWNER_ID = 7011990425

async def transfer(update, context):
    try:
        # Check if the user is the owner
        user_id = update.effective_user.id
        if user_id != OWNER_ID:
            await update.message.reply_text('You are not authorized to use this command.')
            return

        # Ensure the command has the correct number of arguments
        if len(context.args) != 2:
            await update.message.reply_text('Please provide two valid user IDs for the transfer.')
            return

        sender_id = int(context.args[0])
        receiver_id = int(context.args[1])

        # Retrieve sender's and receiver's information
        sender = await user_collection.find_one({'id': sender_id})
        receiver = await user_collection.find_one({'id': receiver_id})

        # Check if both sender and receiver exist
        if not sender:
            await update.message.reply_text(f'Sender with ID {sender_id} not found.')
            return

        if not receiver:
            await update.message.reply_text(f'Receiver with ID {receiver_id} not found.')
            return

        # Transfer all waifus from sender to receiver
        receiver_waifus = receiver.get('characters', [])
        receiver_waifus.extend(sender.get('characters', []))

        # Update receiver's waifus
        await user_collection.update_one({'id': receiver_id}, {'$set': {'characters': receiver_waifus}})

        # Remove waifus from the sender
        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': []}})

        await update.message.reply_text('All waifus transferred successfully!')

    except ValueError:
        await update.message.reply_text('Invalid User IDs provided.')

# Register the transfer command handler
application.add_handler(CommandHandler("transfer", transfer))
