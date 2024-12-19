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

def initialize_mega(email: str, password: str):
    """
    Initialize and log in to Mega account.
    """
    mega = Mega()
    return mega.login(email, password)

async def start_process(client, message):
    """
    Respond to the /start command with a welcome message.
    """
    await message.reply("Welcome to Mega Rename Bot!\nUse /login to log in to your Mega account.")

async def login_process(client, message):
    """
    Handle user login to Mega account.
    """
    try:
        await message.reply("Please send your Mega email.")
        email = (await listen(message.chat.id, app)).text

        await message.reply("Now send your Mega password.")
        password = (await listen(message.chat.id, app)).text

        app.mega = initialize_mega(email, password)
        await message.reply("Mega login successful!")
    except Exception as e:
        logging.error(f"Mega login failed: {str(e)}")
        await message.reply(f"Login failed: {str(e)}")

async def rename_process(client, message):
    """
    Rename files in the user's Mega account based on a given pattern.
    """
    if not hasattr(app, 'mega') or not app.mega.is_logged_in:
        await message.reply("You must be logged in to Mega. Use /login first.")
        return

    try:
        await message.reply("Enter the rename pattern (e.g., 'oldname -> newname'):")
        pattern_message = await listen(message.chat.id, app)
        if not pattern_message or not pattern_message.text:
            await message.reply("No pattern received. Rename process aborted.")
            return

        # Parse rename pattern
        match = re.match(r"(.+)\s*->\s*(.+)", pattern_message.text.strip())
        if not match:
            await message.reply("Invalid rename pattern. Use 'oldname -> newname'.")
            return

        old_pattern, new_pattern = map(str.strip, match.groups())

        # Process renaming
        files = app.mega.get_files()
        renamed_count = 0

        for file in files:
            if re.search(old_pattern, file["name"]):
                new_name = re.sub(old_pattern, new_pattern, file["name"])
                try:
                    app.mega.rename(file["handle"], new_name)
                    renamed_count += 1
                    logging.info(f"Renamed '{file['name']}' to '{new_name}'")
                except Exception as e:
                    logging.error(f"Failed to rename '{file['name']}': {e}")
                    await message.reply(f"Failed to rename '{file['name']}': {e}")

        await message.reply(f"Rename process completed. {renamed_count} files renamed.")
    except Exception as e:
        logging.error(f"Rename failed: {str(e)}")
        await message.reply(f"Rename failed: {str(e)}")

async def listen(chat_id: int, app: Client, timeout: int = 60):
    """
    Listen for a single message from a specific chat within a timeout.
    """
    future = asyncio.get_event_loop().create_future()

    @app.on_message(filters.private & filters.chat(chat_id))
    async def handler(client, message):
        if not future.done():
            future.set_result(message)
        await app.remove_handler(handler)

    try:
        return await asyncio.wait_for(future, timeout)
    except asyncio.TimeoutError:
        logging.error(f"Timeout: No response received within {timeout} seconds.")
        raise Exception("Timeout: No response received.")

health_app = web.Application()
health_app.router.add_get("/health", lambda request: web.Response(text="OK", status=200))

# Run the health server in a separate thread
def start_health_server():
    runner = web.AppRunner(health_app)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, host="0.0.0.0", port=8080)
    loop.run_until_complete(site.start())
    logging.info("Health check server is running...")
    loop.run_forever()

threading.Thread(target=start_health_server, daemon=True).start()

# Command handlers
app.add_handler(MessageHandler(login_process, filters.command("login")))
app.add_handler(MessageHandler(start_process, filters.command("start")))
app.add_handler(MessageHandler(rename_process, filters.command("rename")))

# Run the bot
logging.info("Bot is running...")
app.run()
