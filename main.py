import os
import re
import asyncio
import logging
import threading
from aiohttp import web
from mega import Mega
from pyrogram import Client, filters
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler
from config import BOT_TOKEN, API_ID, API_HASH, MEGA_CREDENTIALS

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger(__name__)

# Initialize the bot
app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
app.mega = Mega()
app.mega_session = None

# Start command
async def start_process(client, message):
    await message.reply("Welcome to Mega Rename Bot!\nUse /login to log in to your Mega account.")

# Login command
async def login_process(client, message):
    try:
        args = message.text.split()
        if len(args) != 3:
            return await message.reply("Format: /login email password")
        email, password = args[1], args[2]
        await message.reply("Logging in... This may take a moment.")
        app.mega_session = await asyncio.to_thread(app.mega.login, email, password)

        if app.mega_session:
            await message.reply("Mega login successful!")
        else:
            await message.reply("Login failed. Please check your credentials.")
    except Exception as e:
        LOGGER.error(f"Mega login failed: {str(e)}")
        await message.reply(f"Login failed: {str(e)}")

# Rename process
async def rename_process(client, message):
    if not app.mega_session:
        await message.reply("You must be logged in to Mega. Use /login first.")
        return

    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply("Format: /rename <new_name>")

        new_base_name = args[1]
        files = await asyncio.to_thread(app.mega.get_files)
        total_files = len(files)
        renamed_count = 0
        failed_files = []  # Track failed files
        update_interval = 10  # Update progress every 10 files
        last_percentage = -1  # Keep track of the last percentage displayed

        reply = await message.reply(f"Renaming files... 0/{total_files}")

        for i, (file_id, file_info) in enumerate(files.items()):
            try:
                old_name = file_info.get('a', {}).get('n', "Unknown Filename")
                base, ext = os.path.splitext(old_name)
                sanitized_new_name = re.sub(r'[\\/*?:"<>|]', "", new_base_name) + ext

                # Corrected rename logic
                await asyncio.to_thread(app.mega.rename, file_id, sanitized_new_name)
                renamed_count += 1

            except (KeyError, TypeError, AttributeError) as e:
                LOGGER.error(f"Error processing file with ID {file_id}: {e}. Skipping this file.")
                failed_files.append(f"ID: {file_id}, Error: {e}")
            except Exception as e:
                LOGGER.error(f"Failed to rename '{old_name if 'old_name' in locals() else 'Unknown File'}': {e}")
                failed_files.append(f"ID: {file_id}, Error: {e}")

            # Update progress
            if (i + 1) % update_interval == 0 or i == len(files) - 1:
                percentage = int((renamed_count / total_files) * 100)
                if percentage != last_percentage:
                    try:
                        await reply.edit_text(f"Renaming files... {percentage}% complete\nPowered by NaughtyX")
                        last_percentage = percentage
                    except Exception as e:
                        LOGGER.error(f"Error editing message: {e}")

        # Summary message
        summary = f"Rename process completed. {renamed_count}/{total_files} files renamed.\nPowered by NaughtyX"
        max_failed_to_show = 10  # Limit the number of failed files displayed
        if failed_files:
            failed_files_to_show = failed_files[:max_failed_to_show]
            error_message = "\n\nThe following files failed to rename:\n" + "\n".join(failed_files_to_show)
            if len(failed_files) > max_failed_to_show:
                error_message += f"\n...and {len(failed_files) - max_failed_to_show} more files failed."
            try:
                await message.reply(error_message)
            except Exception as e:
                LOGGER.error(f"Error sending error message: {e}")

        try:
            await reply.edit_text(summary)
        except Exception as e:
            LOGGER.error(f"Error editing summary message: {e}")

    except Exception as e:
        LOGGER.error(f"Rename failed: {str(e)}")
        await message.reply(f"Rename failed: {str(e)}")

# Health check server
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

# Start health server in a separate thread
threading.Thread(target=start_health_server, daemon=True).start()

# Add handlers
app.add_handler(MessageHandler(login_process, filters.command("login")))
app.add_handler(MessageHandler(start_process, filters.command("start")))
app.add_handler(MessageHandler(rename_process, filters.command("rename")))

# Run the bot
LOGGER.info("Bot is running...")
app.run()
