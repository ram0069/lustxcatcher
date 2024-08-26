from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from shivu import application, top_global_groups_collection, user_collection

async def broadcast(update: Update, context: CallbackContext) -> None:
    OWNER_ID = 7011990425
    
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message_to_broadcast = update.message.reply_to_message

    if message_to_broadcast is None:
        await update.message.reply_text("Please reply to a message to broadcast.")
        return

    all_chats = await top_global_groups_collection.distinct("group_id")
    all_users = await user_collection.distinct("id")

    shuyaa = list(set(all_chats + all_users))

    failed_sends = 0

    for chat_id in shuyaa:
        try:
            await context.bot.forward_message(chat_id=chat_id,
                                              from_chat_id=message_to_broadcast.chat_id,
                                              message_id=message_to_broadcast.message_id)
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {e}")
            failed_sends += 1

    await update.message.reply_text(f"Broadcast complete. Failed to send to {failed_sends} chats/users.")

# Add the command handler
application.add_handler(CommandHandler("broadcast", broadcast, block=False))
