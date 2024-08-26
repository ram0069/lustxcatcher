import os
import random
import html
from html import escape
from pyrogram import filters, types as t
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import shivuu as app
from shivu import application, registered_users

async def help_gift_command(update: Update, context: CallbackContext):
    message = update.message
    sender_id = message.from_user.id
    
    keyboard = [
        [InlineKeyboardButton("Info", callback_data=f'info_{sender_id}'),
         InlineKeyboardButton("Levels", callback_data=f'level_{sender_id}')],
        [InlineKeyboardButton("Games", callback_data=f'game_{sender_id}'),
         InlineKeyboardButton("Gift", callback_data=f'gift_{sender_id}')],
        [InlineKeyboardButton("Slaves", callback_data=f'shadow_army_{sender_id}'),
         InlineKeyboardButton("Beast", callback_data=f'beast_{sender_id}')],
        [InlineKeyboardButton("Pass", callback_data=f'pass_{sender_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    photo_url = "https://te.legra.ph/file/b6661a11573417d03b4b4.png"
    await context.bot.send_photo(
        chat_id=message.chat_id,
        photo=photo_url,
        caption=(
            "<b>SEEKING FOR HELP?</b>\n\n"
            "Well no worries! Click onto the buttons below to get the information that you want!"
        ),
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

# Callback handler for button clicks
async def help_callback_query(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    expected_user_id = int(data.split('_')[-1])

    if user_id != expected_user_id:
        await query.answer("You are not authorized to use this button.", show_alert=True)
        return

    action = '_'.join(data.split('_')[:-1])

    if query.message:
        chat_id = query.message.chat.id

        if action == 'info':
            info_text = (
                "● <b>INFORMATION</b> —\n\n"
                "In this, you will get all the commands associated with checking information.\n"
                "Let's see how it works:\n"
                "• <code>/sinv</code> - To check the user's Token!\n"
                "• <code>/xp</code> - To check the user's levels!\n"
                "• <code>/sinfo</code> - To check the user's full information!\n"
                "• To check the top 10 User in bot!\n"
                "<code>/tops</code> , <code>/topchat</code> , <code>/topgroups</code> , <code>/xtop</code> , <code>/gstop</code>."
            )
            help_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data=f'back_{user_id}')]]
            reply_markup = InlineKeyboardMarkup(help_keyboard)
            await query.message.edit_caption(
                caption=info_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif action == 'level':
            level_text = (
                "● <b>LEVELS</b> —\n\n"
                "Lust bot is having Levels which you can acquire whenever you get involved in bets or else!\n"
                "Check it using any of the following commands:\n"
                "<code>/xp</code>"
            )
            game_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data=f'back_{user_id}')]]
            reply_markup = InlineKeyboardMarkup(game_keyboard)
            await query.message.edit_caption(
                caption=level_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif action == 'beast':
            beast_text = (
                "● <b>BEAST</b> —\n\n"
                "Commands for managing and viewing beasts:\n"
                "• <code>/beastshop</code> - View available beasts in the shop.\n"
                "• <code>/buybeast</code> - Purchase a beast.\n"
                "• <code>/beast</code> - View your beasts.\n"
                "• <code>/binfo</code> - Get information about a specific beast.\n"
                "• <code>/setbeast</code> - Set your main beast."
            )
            beast_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data=f'back_{user_id}')]]
            reply_markup = InlineKeyboardMarkup(beast_keyboard)
            await query.message.edit_caption(
                caption=beast_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif action == 'pass':
            pass_text = (
                "● <b>SLAVE PASS</b> —\n\n"
                "<code>/pass</code> - a premium membership of bot with exciting rewards.\n"
                "<b>How to Use Pass?</b> \n\n"
                "‼️ <code>/claim</code> - with this you can get a reward for the week.\n"
                "‼️ <code>/sweekly</code> - to use this you must use <code>/claim</code> 6 times a week.\n"
                "‼️ <code>/pbonus</code> - to use this you must complete the tasks it says."
            )
            pass_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data=f'back_{user_id}')]]
            reply_markup = InlineKeyboardMarkup(pass_keyboard)
            await query.message.edit_caption(
                caption=pass_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif action == 'game':
            game_text = (
                "● <b>GAMES</b> —\n\n"
                "You can now stake your WEALTH Cash and win extra with it! This will also help in getting more XP as well!\n"
                "The various commands associated with it are as follows:\n"
                "• Coin Toss - To do a coin toss bet by guessing its result as heads or tails! <code>/sbet 10000 heads</code>\n"
                "• Dice Roll - To do a dice roll bet by guessing its result as odd or even! <code>/roll 10000 even</code>\n"
                "• Gamble - To do a Gamble bet by guessing its result as right or left! <code>/gamble 10000 l</code>\n"
                "• Basketball - To do a basketball bet based on 🏀 emoji! <code>/basket 10000</code>\n"
                "• Dart - To do a dart bet based on 🎯 emoji! <code>/dart 10000</code>\n"
                "• <b>Stour</b> - To do contract with slaves with the base of contract crystal <code>/stour</code>\n"
                "• <b>Riddle</b> - A Mathematics-based game system where you can earn tokens <code>/riddle</code>."
            )
            game_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data=f'back_{user_id}')]]
            reply_markup = InlineKeyboardMarkup(game_keyboard)
            await query.message.edit_caption(
                caption=game_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif action == 'gift':
            gift_text = (
                "● <b>GIFTS</b> —\n\n"
                "You can pay hunters some of your Wealth Cash to them! Just reply <code>/pay</code> followed by amount!\n"
                "Note that You can pay up to ₩<code>70,000,000,000</code> in every 20 minutes!\n"
                "You can also get some free WEALTH cash for your own. Try <code>/daily</code>,<code>/weekly</code>."
            )
            beast_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data=f'back_{user_id}')]]
            reply_markup = InlineKeyboardMarkup(beast_keyboard)
            await query.message.edit_caption(
                caption=gift_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif action == 'shadow_army':
            army_text = (
                "● <b>Slaves</b> —\n\n"
                "Lust bot spawns random slaves in your chat after every 100 messages.\n"
                "Add them in your harem by sending <code>/slave</code> and their name. The first user who tells the correct name will get that slave.\n"
                "View your slaves using: <code>/myslave</code>.\n"
                "<code>/smode</code> to sort slaves by rank, etc."
            )
            beast_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data=f'back_{user_id}')]]
            reply_markup = InlineKeyboardMarkup(beast_keyboard)
            await query.message.edit_caption(
                caption=army_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif action == 'back':
            caption = (
                "<b>SEEKING FOR HELP?</b>\n\n"
                "Well no worries! Click on the buttons below to get the information that you want!"
            )
            keyboard = [
                [InlineKeyboardButton("Info", callback_data=f'info_{user_id}'),
                 InlineKeyboardButton("Levels", callback_data=f'level_{user_id}')],
                [InlineKeyboardButton("Games", callback_data=f'game_{user_id}'),
                 InlineKeyboardButton("Gift", callback_data=f'gift_{user_id}')],
                [InlineKeyboardButton("Slaves", callback_data=f'shadow_army_{user_id}'),
                 InlineKeyboardButton("Beast", callback_data=f'beast_{user_id}')],
                [InlineKeyboardButton("Pass", callback_data=f'pass_{user_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_caption(
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )

application.add_handler(CommandHandler("help", help_gift_command))
application.add_handler(CallbackQueryHandler(help_callback_query, pattern='info_\d+|level_\d+|beast_\d+|pass_\d+|game_\d+|gift_\d+|shadow_army_\d+|back_\d+', block=False))
