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
from concurrent.futures import ThreadPoolExecutor
from config import BOT_TOKEN, API_ID, API_HASH

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger(__name__)

# Initialize the bot
app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
app.mega = Mega()
app.mega_session = None
app.executor = ThreadPoolExecutor(max_workers=20)  # For parallel renaming

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

# Helper function to extract file names
def extract_file_name(file_info):
    try:
        return file_info['a']['n']
    except (KeyError, TypeError):
        return None

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
        all_files = await asyncio.to_thread(app.mega_session.get_files)
        total_files = len(all_files)
        renamed_count = 0
        failed_files = []

        reply = await message.reply(f"Renaming files... 0/{total_files}")

        async def rename_single_file(file_info, file_number):
            nonlocal renamed_count, failed_files
            original_file_name = extract_file_name(file_info)
            if not original_file_name:
                failed_files.append(f"File ID {file_info}: Could not extract filename")
                return
            new_name = f"{new_base_name}_{file_number}{os.path.splitext(original_file_name)[-1]}"
            try:
                file_id = next(k for k, v in all_files.items() if v == file_info)
                app.mega_session.rename(file_id, new_name)
                renamed_count += 1
            except Exception as e:
                failed_files.append(f"File {original_file_name}: {e}")

        futures = [
            app.executor.submit(rename_single_file, file_info, i + 1)
            for i, (k, file_info) in enumerate(all_files.items())
        ]
        for future in asyncio.as_completed(futures):
            await asyncio.sleep(0)  # Yield control
            await reply.edit_text(f"Renaming files... {renamed_count}/{total_files} done")

        await reply.edit_text(f"Rename process completed. {renamed_count}/{total_files} files renamed.")
        if failed_files:
            error_message = "\n\nThe following files failed to rename:\n" + "\n".join(failed_files[:10])
            if len(failed_files) > 10:
                error_message += f"\n...and {len(failed_files) - 10} more files failed."
            await message.reply(error_message)

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
