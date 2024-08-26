from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import user_collection, refeer_collection, application 

async def refer(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    referral_link = f"https://t.me/lustXcatcherrobot?start=r_{user_id}"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Share this referral link with your friends:\n1 refer = 1000 tokans and other user get 500.\n{referral_link}")

application.add_handler(CommandHandler("refer", refer))
