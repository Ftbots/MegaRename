import os
import re
import asyncio
import logging
from aiohttp import web
from mega import Mega
from pyrogram import Client, filters
from pyrogram.filters import command, private
from pyrogram.handlers import MessageHandler
from config import BOT_TOKEN, API_ID, API_HASH, MEGA_CREDENTIALS

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("pyrogram").setLevel(ERROR)
LOGGER = getLogger(__name__)
# Initialize the bot
app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

def initialize_mega(email: str, password: str):
    """
    Initialize and log in to Mega account.
    """
    mega = Mega()
    return mega.login(email, password)

async def start(client, message):
    """
    Respond to the /start command with a welcome message.
    """
    await message.reply("Welcome to Mega Rename Bot!\nUse /login to log in to your Mega account.")

async def login(client, message):
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

async def rename(client, message):
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

async def health_check(request):
    """
    Respond to health check requests.
    """
    return web.Response(text="OK", status=200)

def create_health_server():
    """
    Create a health check web server.
    """
    health_app = web.Application()
    health_app.router.add_get("/health", health_check)
    return health_app

async def main():
    """
    Main function to run the bot and health check server.
    """
    health_server = create_health_server()
    runner = web.AppRunner(health_server)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=8080)
    await site.start()

    await app.start()
    app.add_handler(MessageHandler(login, filters=command("login")))
    app.add_handler(MessageHandler(start, filters=command("start")))
    app.add_handler(MessageHandler(rename, filters=command("rename")))
    logging.info("Bot is running...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
