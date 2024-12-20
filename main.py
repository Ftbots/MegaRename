import os
import re
import asyncio
import logging
import threading
from aiohttp import web
from mega import Mega
from pyrogram import Client, filters
from pyrogram.filters import command, private
from pyrogram.handlers import MessageHandler
from config import BOT_TOKEN, API_ID, API_HASH, MEGA_CREDENTIALS  # Your config file

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("pyrogram").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

# Initialize the bot
app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
app.mega = Mega()
app.mega_session = None

async def start_process(client, message):
    """Respond to the /start command."""
    await message.reply("Welcome to Mega Rename Bot!\nUse /login to log in to your Mega account.")

async def login_process(client, message):
    """Handle user login to Mega account."""
    try:
        args = message.text.split()
        if len(args) != 3:
            return await message.reply("Format: /login email password")
        email, password = args[1], args[2]
        app.mega_session = app.mega.login(email, password)
        if app.mega_session:
            await message.reply("Mega login successful!")
        else:
            await message.reply("Login failed. Please check your credentials.")
    except Exception as e:
        LOGGER.error(f"Mega login failed: {str(e)}")
        await message.reply(f"Login failed: {str(e)}")

async def rename_process(client, message):
    """Rename files, preserving file extensions, with improved error handling and progress update."""
    if not app.mega_session:
        await message.reply("You must be logged in to Mega. Use /login first.")
        return

    try:
        # ... (rest of rename_process function remains unchanged) ...
    except Exception as e:
        LOGGER.error(f"Rename failed: {str(e)}")
        await message.reply(f"Rename failed: {str(e)}")


async def getinfo_process(client, message):
    """Get Mega account information."""
    if not app.mega_session:
        await message.reply("You must be logged in to Mega. Use /login first.")
        return

    try:
        account_info = app.mega.get_user_info()
        if account_info:
            storage_info = app.mega.get_storage_info()  # added to get storage details

            response = f"**Mega Account Information:**\n"
            response += f"Username: {account_info['email']}\n"
            response += f"Storage Used: {storage_info['used']:.2f} GB\n"  # formatted
            response += f"Storage Total: {storage_info['total']:.2f} GB\n"  # formatted
            response += f"Storage Free: {storage_info['free']:.2f} GB\n"  # formatted
            response += f"Total Files: {len(app.mega.get_files())}\n" # added total files count


            await message.reply(response)
        else:
            await message.reply("Failed to retrieve account information.")
    except Exception as e:
        LOGGER.error(f"Get info failed: {str(e)}")
        await message.reply(f"Get info failed: {str(e)}")


# Health check server (optional)
# ... (health check server code remains unchanged) ...

# Command handlers
app.add_handler(MessageHandler(login_process, filters.command("login")))
app.add_handler(MessageHandler(start_process, filters.command("start")))
app.add_handler(MessageHandler(rename_process, filters.command("rename")))
app.add_handler(MessageHandler(getinfo_process, filters.command("getinfo"))) #added handler for /getinfo

# Run the bot
LOGGER.info("Bot is running...")
app.run()
