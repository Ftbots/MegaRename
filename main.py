import os
import asyncio
import logging
import threading
from aiohttp import web
from mega import Mega
from pyrogram import Client, filters
from config import BOT_TOKEN, API_ID, API_HASH

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger(__name__)

# Initialize the bot
app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
mega = Mega()
mega_session = None

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
    LOGGER.info("Health check server running...")
    loop.run_forever()

threading.Thread(target=start_health_server, daemon=True).start()

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Welcome! Use /login to log in to your Mega account.")

@app.on_message(filters.command("login"))
async def login(client, message):
    global mega_session
    try:
        args = message.text.split(maxsplit=2)
        if len(args) != 3:
            return await message.reply("Format: /login email password")
        email, password = args[1], args[2]
        mega_session = mega.login(email, password)
        await message.reply("Login successful!")
    except Exception as e:
        LOGGER.error(f"Login failed: {e}")
        await message.reply(f"Login failed: {e}")

@app.on_message(filters.command("rename"))
async def rename_files(client, message):
    global mega_session
    if not mega_session:
        return await message.reply("You must log in first. Use /login email password.")

    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        return await message.reply("Format: /rename new_name")

    new_name = args[1].strip()
    if not new_name:
        return await message.reply("New name cannot be empty.")

    try:
        files = mega_session.get_files()
        if not files:
            return await message.reply("No files found in your Mega account.")

        renamed_count = 0
        for index, (file_id, file_info) in enumerate(files.items(), start=1):
            try:
                # Validate file_info structure
                if not isinstance(file_info, dict):
                    LOGGER.warning(f"Invalid file_info for file ID {file_id}")
                    continue

                attributes = file_info.get("a")
                if not attributes or not isinstance(attributes, dict):
                    LOGGER.warning(f"Missing attributes in file_info for file ID {file_id}")
                    continue

                file_name = attributes.get("n")
                if not file_name:
                    LOGGER.warning(f"File name not found for file ID {file_id}")
                    continue

                # Extract file extension
                file_extension = os.path.splitext(file_name)[1]
                renamed_file_name = f"{new_name}_{index}{file_extension}"

                # Rename file
                mega_session.rename(file_id, renamed_file_name)
                renamed_count += 1
                LOGGER.info(f"Renamed '{file_name}' to '{renamed_file_name}'")
            except Exception as e:
                LOGGER.error(f"Failed to rename file {file_id}: {e}")

        await message.reply(f"Renaming complete. Total files renamed: {renamed_count}")
    except Exception as e:
        LOGGER.error(f"Error during renaming: {e}")
        await message.reply(f"Error: {e}")

# Run the bot
if __name__ == "__main__":
    LOGGER.info("Starting bot...")
    app.run()
