from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from pyrogram import Client, filters
from shivu import user_collection, collection, application
import asyncio
import random
from datetime import datetime, timedelta

# Dictionary to store active riddles
active_riddles = {}
# Dictionary to store user cooldowns
user_cooldowns = {}

# List of random image URLs
image_urls = [
    "https://telegra.ph/file/7959c4cb32a33ceda8077.png",
    "https://telegra.ph/file/28219cc76de077a48d110.png",
    "https://telegra.ph/file/06f49ccbf0fda31ad8a6e.png",
    # Add more image URLs as needed
]

# Command handler to start the riddle
async def start_riddle_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    current_time = datetime.now()

    # Check if the user is on cooldown
    if user_id in user_cooldowns and current_time < user_cooldowns[user_id]:
        remaining_time = (user_cooldowns[user_id] - current_time).total_seconds()
        await update.message.reply_text(f"Please wait {int(remaining_time)} seconds before starting a new riddle.")
        return

    # Generate a varied math question with addition, subtraction, multiplication, or division
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    num3 = random.randint(1, 10)
    operators = ['+', '-', '*', '/']
    op1 = random.choice(operators)
    op2 = random.choice(operators)
    
    # Ensure division does not result in fractions or division by zero
    if op2 == '/' and num3 == 0:
        num3 = 1

    # Generate the expression and calculate the result
    expression = f"{num1} {op1} {num2} {op2} {num3}"
    result = eval(expression)

    # Check if the result is an integer; if not, regenerate the question
    while not isinstance(result, int):
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        num3 = random.randint(1, 10)
        op1 = random.choice(operators)
        op2 = random.choice(operators)

        if op2 == '/' and num3 == 0:
            num3 = 1

        expression = f"{num1} {op1} {num2} {op2} {num3}"
        result = eval(expression)

    correct_answer = result
    question = f"( {num1} {op1} {num2} ) {op2} {num3} = ?🧐\n\nAnswer in 15 sec."

    # Generate answer options
    answers = [correct_answer, correct_answer + random.randint(1, 10), correct_answer - random.randint(1, 10), correct_answer + random.randint(11, 20)]
    random.shuffle(answers)

    # Store the active riddle
    active_riddles[user_id] = {
        'question': question,
        'correct_answer': correct_answer,
        'start_time': current_time
    }

    # Create buttons in a 2x2 layout
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(str(answers[0]), callback_data=f'riddle_answer_{user_id}_{answers[0]}'), InlineKeyboardButton(str(answers[1]), callback_data=f'riddle_answer_{user_id}_{answers[1]}')],
            [InlineKeyboardButton(str(answers[2]), callback_data=f'riddle_answer_{user_id}_{answers[2]}'), InlineKeyboardButton(str(answers[3]), callback_data=f'riddle_answer_{user_id}_{answers[3]}')]
        ]
    )

    # Select a random image
    image_url = random.choice(image_urls)

    # Send the question with the image
    sent_message = await context.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=image_url,
        caption=question,
        reply_markup=keyboard
    )

    # Schedule timeout
    asyncio.create_task(riddle_timeout(context, user_id, sent_message.chat_id, sent_message.message_id))

# Function to handle riddle timeout
async def riddle_timeout(context: CallbackContext, user_id: int, chat_id: int, message_id: int):
    await asyncio.sleep(15)

    if user_id in active_riddles:
        correct_answer = active_riddles[user_id]['correct_answer']
        del active_riddles[user_id]

        try:
            await context.bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=f"Time out! The correct answer was {correct_answer}."
            )
        except Exception as e:
            print(f"Failed to edit message: {e}")

# Callback handler to process the riddle answer
async def riddle_answer_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split('_')
    riddle_user_id = int(data[2])
    answer = float(data[3])  # Convert answer to float to handle division results

    if user_id != riddle_user_id:
        await query.answer("This riddle is not for you.", show_alert=True)
        return

    if riddle_user_id not in active_riddles:
        await query.answer("You are not currently participating in any riddle.", show_alert=True)
        return

    correct_answer = active_riddles[riddle_user_id]['correct_answer']

    # Allow for a small tolerance for floating-point comparison
    tolerance = 1e-6
    if abs(answer - correct_answer) < tolerance:
        # Correct answer
        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': 80}})
        await query.message.edit_caption("Correct answer! You got 80 tokens.")
    else:
        # Incorrect answer
        await query.message.edit_caption(f"Incorrect answer. The correct answer was {correct_answer}.")

    # Remove the active riddle
    del active_riddles[riddle_user_id]
    # Set user cooldown for 30 seconds
    user_cooldowns[riddle_user_id] = datetime.now() + timedelta(seconds=30)

# Add command handler for starting riddles
application.add_handler(CommandHandler("riddle", start_riddle_cmd, block=False))
# Add callback query handler for riddle answers
application.add_handler(CallbackQueryHandler(riddle_answer_callback, pattern=r'riddle_answer_', block=False))
