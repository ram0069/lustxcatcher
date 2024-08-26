import sys
import io
import os
from pyrogram import filters
from shivu import shivuu as app

# Define the owner IDs (use integers for Telegram user IDs)
OWNER_IDS = [7011990425]

async def aexec(code, message):
    exec(f"async def __aexec(message): " + "".join(f"\n {l}" for l in code.split("\n")))
    return await locals()["__aexec"](message)

@app.on_message(filters.command("eval", prefixes="."))
async def evals(_, message):
    user_id = message.from_user.id
    
    # Check if the user is an owner
    if user_id not in OWNER_IDS:
        await message.reply_text("You are not authorized to use this command.")
        return

    parts = message.text.split(" ", maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("No code provided to evaluate.")
        return

    to_eval = parts[1]

    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    stdout = None

    try:
        await aexec(to_eval, message)
        stdout = redirected_output.getvalue()
    except Exception as e:
        stdout = f"Exception occurred: {e}"
    finally:
        sys.stdout = old_stdout

    if stdout:
        final_output = f"```eval\n{stdout.strip()}\n```"
        if len(final_output) > 4095:
            with io.BytesIO(str.encode(stdout)) as out_file:
                out_file.name = "eval.txt"
                await app.send_document(message.chat.id, document=out_file, caption=to_eval)
                os.remove("eval.txt")
        else:
            await message.reply_text(final_output)
    else:
        await message.reply_text("No output.")
        
