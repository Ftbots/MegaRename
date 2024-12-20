import os
import re
import asyncio
import logging
from aiohttp import web
from mega import Mega  # Assume this library is used
from pyrogram import Client, filters
from pyrogram.filters import command, private
from pyrogram.handlers import MessageHandler
from config import BOT_TOKEN, API_ID, API_HASH, MEGA_CREDENTIALS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("pyrogram").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
app.mega = Mega()
app.mega_session = None

async def start_process(client, message):
    await message.reply("Welcome to Mega Rename Bot!nUse /login to log in to your Mega account.")

async def login_process(client, message):
    try:
        args = message.text.split()
        if len(args) != 3:
            return await message.reply("Format: /login email password")
        email, password = args[1], args[2]
        await message.reply("Logging in... This may take a moment.") # Inform user
        app.mega_session = await asyncio.to_thread(app.mega.login, email, password) # Use asyncio.to_thread for blocking operation

        if app.mega_session:
            await message.reply("Mega login successful!")
        else:
            await message.reply("Login failed. Please check your credentials.")
    except Exception as e:
        LOGGER.error(f"Mega login failed: {str(e)}")
        await message.reply(f"Login failed: {str(e)}")

async def rename_process(client, message):
    if not app.mega_session:
        await message.reply("You must be logged in to Mega. Use /login first.")
        return

    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply("Format: /rename <new_name>")

        new_base_name = args[1]
        batch_size = 50  # Adjust this based on API limits and performance

        files = await asyncio.to_thread(app.mega.get_files) # Get all files upfront
        total_files = len(files)
        reply = await message.reply(f"Renaming files... 0/{total_files}")
        renamed_count = 0

        for i in range(0, total_files, batch_size):
            batch = list(files.items())[i:i + batch_size]
            try:
                # Implement batch renaming here. This is the most critical part.
                # You'll likely need a custom function or modification to the 'mega' library.
                # This example assumes a hypothetical `batch_rename` method exists in the `mega` library.
                await asyncio.to_thread(app.mega.batch_rename, batch, new_base_name)
                renamed_count += len(batch)
                await reply.edit_text(f"Renaming files... {renamed_count}/{total_files}\nPowered by NaughtyX")
            except Exception as e:
                LOGGER.error(f"Batch rename failed: {e}")
                await reply.edit_text(f"Batch rename failed: {e}\nContinuing with other files...\nPowered by NaughtyX")

        await reply.edit_text(f"Rename process completed. {renamed_count}/{total_files} files renamed.\nPowered by NaughtyX")

    except Exception as e:
        LOGGER.error(f"Rename failed: {str(e)}")
        await message.reply(f"Rename failed: {str(e)}")

# Health check server (optional)
# ... (rest of the code remains the same)

app.add_handler(MessageHandler(login_process, filters.command("login")))
app.add_handler(MessageHandler(start_process, filters.command("start")))
app.add_handler(MessageHandler(rename_process, filters.command("rename")))

LOGGER.info("Bot is running...")
app.run()
