from pyrogram import Client, filters
import random
import string
from datetime import datetime
from shivu import user_collection, application, collection 
from shivu import shivuu as app
from shivu import shivuu as bot
from telegram.constants import ParseMode

# Dictionary to store generated codes and their amounts, and user claims
generated_codes = {}

# Function to generate a random string of length 10
def generate_random_code():
    return ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=10))

# Function to generate a random amount within the specified range
def generate_random_amount():
    return random.randint(10, 5000000000)

@app.on_message(filters.command(["gen"]))
async def gen(client, message):
    sudo_user_id = 7011990425
    if message.from_user.id != sudo_user_id:
        await message.reply_text("Only authorized users can use this command.")
        return
    
    try:
        amount = float(message.command[1])  # Get the amount from the command
        quantity = int(message.command[2])  # Get the quantity from the command
    except (IndexError, ValueError):
        await message.reply_text("Invalid amount or quantity. Usage: return `/gen 10000000 5`")
        return
    
    # Generate a random code
    code = generate_random_code()
    
    # Store the generated code and its associated amount and quantity
    generated_codes[code] = {'amount': amount, 'quantity': quantity, 'claimed_by': []}
    
    # Format the amount with commas and remove unnecessary decimal places
    formatted_amount = f"{amount:,.0f}" if amount.is_integer() else f"{amount:,.2f}"
    
    await message.reply_text(
        f"Generated code: `{code}`\nAmount: `{formatted_amount}`\nQuantity: `{quantity}`"
    )

@app.on_message(filters.command(["redeem"]))
async def redeem(client, message):
    code = " ".join(message.command[1:])  # Get the code from the command
    user_id = message.from_user.id
    
    if code in generated_codes:
        code_info = generated_codes[code]
        
        # Check if the user has already claimed this code
        if user_id in code_info['claimed_by']:
            await message.reply_text("You have already claimed this code.")
            return
        
        # Check if there are claims remaining for the code
        if len(code_info['claimed_by']) >= code_info['quantity']:
            await message.reply_text("This code has been fully claimed.")
            return
        
        # Update the user's balance
        await user_collection.update_one(
            {'id': user_id},
            {'$inc': {'balance': float(code_info['amount'])}}  # Convert amount to float before updating
        )
        
        # Add user to the claimed_by list
        code_info['claimed_by'].append(user_id)
        
        # Format the amount with commas and remove unnecessary decimal places
        formatted_amount = f"{code_info['amount']:,.0f}" if code_info['amount'].is_integer() else f"{code_info['amount']:,.2f}"
        
        await message.reply_text(
            f"Redeemed successfully. ₩`{formatted_amount}` Cash added to your Wealth."
        )
    else:
        await message.reply_text("Invalid code.")

pending_trades = {}
pending_gifts = {}
generated_waifus = {}

# Sudo user IDs
sudo_user_ids = ["7011990425"]

# Function to generate a random string of length 10 composed of random letters and digits
def generate_random_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

@bot.on_message(filters.command(["sgen"]))
async def waifugen(client, message):
    if str(message.from_user.id) not in sudo_user_ids:
        await message.reply_text("You are not authorized to generate waifus.")
        return
    
    try:
        character_id = message.command[1]  # Get the character_id from the command
        quantity = int(message.command[2])  # Get the quantity from the command
    except (IndexError, ValueError):
        await message.reply_text("Invalid usage. Usage: `/sgen 56 1`")
        return

    # Retrieve the waifu with the given character_id
    waifu = await collection.find_one({'id': character_id})
    if not waifu:
        await message.reply_text("Invalid character ID. Waifu not found.")
        return

    code = generate_random_code()
    
    # Store the generated waifu and its details
    generated_waifus[code] = {'waifu': waifu, 'quantity': quantity}
    
    response_text = (
        f"Generated code: `{code}`\n"
        f"Name: {waifu['name']}\nRarity: {waifu['rarity']}\nQuantity: {quantity}"
    )
    
    await message.reply_text(response_text)

@bot.on_message(filters.command(["sredeem"]))
async def claimwaifu(client, message):
    code = " ".join(message.command[1:])  # Get the code from the command
    user_id = message.from_user.id
    user_mention = f"[{message.from_user.first_name}](tg://user?id={user_id})"

    if code in generated_waifus:
        details = generated_waifus[code]
        
        if details['quantity'] > 0:
            waifu = details['waifu']
            
            # Update the user's characters collection
            await user_collection.update_one(
                {'id': user_id},
                {'$push': {'characters': waifu}}
            )
            
            # Decrement the remaining quantity
            details['quantity'] -= 1
            
            # Remove the code if its quantity is 0
            if details['quantity'] == 0:
                del generated_waifus[code]
            
            response_text = (
                f"Congratulations {user_mention}! You have received a new Slave!\n"
                f"Name: {waifu['name']}\n"
                f"Rarity: {waifu['rarity']}\n"
                f"Anime: {waifu['anime']}\n"
            )
            await message.reply_photo(photo=waifu['img_url'], caption=response_text)
        else:
            await message.reply_text("This code has already been claimed the maximum number of times.")
    else:
        await message.reply_text("Invalid code.")
