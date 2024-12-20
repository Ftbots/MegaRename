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

#Helper function to recursively get folder details
def get_folder_details(mega_instance, folder_id = "root"):
    folder_details = {}
    folder_details["folders"] = []
    try:
      files = mega_instance.get_files(folder_id)
      if files:
          for file_id, file_info in files.items():
              if file_info['t'] == 0: # 0 indicates folder in Mega
                  folder_details["folders"].append(file_info["a"]["n"])
                  # Recursive call to get subfolders details, you may want to limit recursion depth
                  folder_details["folders"].extend(get_folder_details(mega_instance, file_id)["folders"])
      folder_details["total_folders"] = len(folder_details["folders"])

      return folder_details
    except Exception as e:
      LOGGER.error(f"Error getting folder details: {e}")
      return {"total_folders": 0, "folders": []}

async def start_process(client, message):
    await message.reply("Welcome to Mega Rename Bot!\nUse /login to log in to your Mega account. Use /getinfo to get folder information.")

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
    # ... (rest of rename_process remains the same)

async def getinfo_process(client, message):
    if not app.mega_session:
        await message.reply("You must be logged in to Mega. Use /login first.")
        return

    try:
        folder_info = get_folder_details(app.mega)
        reply_message = f"Total Folders: {folder_info['total_folders']}\n"
        if folder_info['folders']:
            reply_message += "Folder Names:\n"
            reply_message += "\n".join(folder_info['folders'])
        else:
            reply_message += "No folders found."
        await message.reply(reply_message)

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
