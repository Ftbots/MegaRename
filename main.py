
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
        args = message.text.split()
        if len(args) != 2:
            return await message.reply("Format: /rename <new_name>")

        new_base_name = args[1]
        files = app.mega.get_files()
        total_files = len(files)
        renamed_count = 0
        reply = await message.reply(f"Renaming files... 0/{total_files}")  # Initial message

        for file_id, file_info in files.items():
            try:
                old_name = file_info['a']['n'] if 'a' in file_info and 'n' in file_info['a'] else "Unknown Filename"
                base, ext = os.path.splitext(old_name)
                sanitized_new_name = re.sub(r'[\\/*?:"<>|]', "", new_base_name) + ext

                app.mega.rename((file_id, file_info), sanitized_new_name)
                renamed_count += 1
                await reply.edit(f"Renaming files... {renamed_count}/{total_files}")  # Update message
                LOGGER.info(f"Renamed '{old_name}' to '{sanitized_new_name}'")
            except (KeyError, TypeError) as e:
                LOGGER.error(f"Error accessing file information for ID {file_id}: {e}. Skipping this file.")
                await reply.edit(f"Error processing file with ID {file_id}. Skipping...\nContinuing with other files...")
            except Exception as e:
                LOGGER.error(f"Failed to rename '{old_name if 'old_name' in locals() else 'Unknown File'}': {e}")
                await reply.edit(f"Failed to rename '{old_name if 'old_name' in locals() else 'Unknown File'}': {e}\nContinuing with other files...")

        await reply.edit(f"Rename process completed. {renamed_count} files renamed.")

    except Exception as e:
        LOGGER.error(f"Rename failed: {str(e)}")
        await message.reply(f"Rename failed: {str(e)}")


async def get_file_list_process(client, message):
    """Lists files in the Mega account."""
    if not app.mega_session:
        await message.reply("You must be logged in to Mega. Use /login first.")
        return

    try:
        files = app.mega.get_files()
        file_list = ""
        for file_id, file_info in files.items():
            file_name = file_info['a']['n'] if 'a' in file_info and 'n' in file_info['a'] else "Unknown Filename"
            file_list += f"- {file_name}\n"
        await message.reply(f"Files in your Mega account:\n{file_list}")
    except Exception as e:
        LOGGER.error(f"Failed to get file list: {e}")
        await message.reply(f"Failed to get file list: {e}")


async def download_file_process(client, message):
    if not app.mega_session:
        await message.reply("You must be logged in to Mega. Use /login first.")
        return
    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply("Format: /download <file_name>")
        file_name = args[1]
        files = app.mega.get_files()
        for file_id, file_info in files.items():
            if file_info['a']['n'] == file_name:
                file_url = app.mega.get_download_link(file_id)
                await message.reply(f"Download Link for {file_name}:\n{file_url}")
                return
        await message.reply(f"File '{file_name}' not found.")

    except Exception as e:
        LOGGER.error(f"Download process failed: {e}")
        await message.reply(f"Download process failed: {e}")



# Health check server (optional)
health_app = web.Application()
health_app.router.add_get("/health", lambda request: web.Response(text="OK", status=200))


def start_health_server():
    runner = web.AppRunner(health_app)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, host="0.0.0.0", port=8080)
    loop.run_until_complete(site.start())
    LOGGER.info("Health check server is running...")
    loop.run_forever()


threading.Thread(target=start_health_server, daemon=True).start()

# Command handlers
app.add_handler(MessageHandler(login_process, filters.command("login")))
app.add_handler(MessageHandler(start_process, filters.command("start")))
app.add_handler(MessageHandler(rename_process, filters.command("rename")))
app.add_handler(MessageHandler(get_file_list_process, filters.command("list")))
app.add_handler(MessageHandler(download_file_process, filters.command("download")))

# Run the bot
LOGGER.info("Bot is running...")
app.run()

