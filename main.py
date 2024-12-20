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
from config import BOT_TOKEN, API_ID, API_HASH, MEGA_CREDENTIALS

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("pyrogram").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

# Initialize the bot
app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
app.mega = Mega()
app.mega_session = None


def get_mega_details(mega_instance, node_id="root", level=0, max_depth=5, indent=""): #Added max_depth to limit recursion
    """Recursively retrieves file and folder details."""
    try:
        details = mega_instance.get_files(node_id)
        file_info_list = []
        if details:
            for file_id, file_info in details.items():
                file_type = "file" if file_info["t"] == 1 else "folder"
                file_info_list.append({
                    "name": file_info["a"]["n"],
                    "type": file_type,
                    "size": file_info["s"] if "s" in file_info else "N/A",  # Handle missing size
                    "id": file_id,
                    "path": indent + file_info["a"]["n"]
                })
                if file_type == "folder" and level < max_depth: #Recursive call for folders, with depth limit
                    file_info_list.extend(get_mega_details(mega_instance, file_id, level + 1, max_depth, indent + "  "))
        return file_info_list
    except Exception as e:
        LOGGER.error(f"Error getting Mega details: {e}")
        return []


async def start_process(client, message):
    await message.reply("Welcome to Mega Rename Bot!nUse /login to log in to your Mega account. Use /getinfo to get file/folder information.")


async def login_process(client, message):
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
    if not app.mega_session:
        await message.reply("You must be logged in to Mega. Use /login first.")
        return
    # ... (rename_process remains unchanged)


async def getinfo_process(client, message):
    if not app.mega_session:
        await message.reply("You must be logged in to Mega. Use /login first.")
        return

    try:
        all_details = get_mega_details(app.mega)
        if not all_details:
            await message.reply("No files or folders found.")
            return

        reply_message = "Mega File/Folder Information:n"
        for item in all_details:
            reply_message += f"Path: {item['path']}, Type: {item['type']}, Size: {item['size']}n"

        await message.reply(reply_message)  #Send the entire list

    except Exception as e:
        LOGGER.error(f"Get info failed: {str(e)}")
        await message.reply(f"Get info failed: {str(e)}")


# Health check server (optional)
# ... (health check server code remains the same)

# Command handlers
app.add_handler(MessageHandler(login_process, filters.command("login")))
app.add_handler(MessageHandler(start_process, filters.command("start")))
app.add_handler(MessageHandler(rename_process, filters.command("rename")))
app.add_handler(MessageHandler(getinfo_process, filters.command("getinfo")))

# Run the bot
LOGGER.info("Bot is running...")
app.run()
