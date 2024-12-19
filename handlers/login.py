from pyrogram.filters import command, private
from pyrogram.types import Message
from mega import Mega
from config import MEGA_CREDENTIALS
from utils import listen
import logging

@app.on_message(command("login") & private)
async def login(client, message):
    await message.reply("Please send your Mega email.")
    email_message = await listen(message.chat.id, app)
    email = email_message.text
    
    await message.reply("Now send your Mega password.")
    password_message = await listen(message.chat.id, app)
    password = password_message.text

    try:
        mega = Mega()
        mega.login(email, password)
        # Store mega instance for later use.  This is crucial
        app.mega = mega  
        await message.reply("Mega login successful!")
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        await message.reply(f"Login failed: {str(e)}")
