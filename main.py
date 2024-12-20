import os
import re
import logging
from mega import Mega
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from config import BOT_TOKEN, API_ID, API_HASH

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

async def getinfo_process(client, message):
    """Get Mega account information."""
    if not app.mega_session:
        await message.reply("You must be logged in to Mega. Use /login first.")
        return

    try:
        account_info = app.mega.get_user_info()
        if account_info:
            storage_info = app.mega.get_storage_info()

            response = f"**Mega Account Information:**\n"
            response += f"Username: {account_info['email']}\n"
            response += f"Storage Used: {storage_info['used']:.2f} GB\n"
            response += f"Storage Total: {storage_info['total']:.2f} GB\n"
            response += f"Storage Free: {storage_info['free']:.2f} GB\n"
            response += f"Total Files: {len(app.mega.get_files())}\n"

            await message.reply(response)
        else:
            await message.reply("Failed to retrieve account information.")
    except Exception as e:
        LOGGER.error(f"Get info failed: {str(e)}")
        await message.reply(f"Get info failed: {str(e)}")

# Command handlers
app.add_handler(MessageHandler(start_process, filters.command("start")))
app.add_handler(MessageHandler(login_process, filters.command("login")))
app.add_handler(MessageHandler(rename_process, filters.command("rename")))
app.add_handler(MessageHandler(getinfo_process, filters.command("getinfo")))

# Run the bot
LOGGER.info("Bot is running...")
app.run()
