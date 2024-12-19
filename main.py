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

def get_all_files(mega_instance):
    """Recursively fetch all files from the Mega account."""
    files = []

    def explore_folder(folder_id):
        folder_files = mega_instance.get_files()
        for file_id, file_info in folder_files.items():
            if "t" in file_info and file_info["t"] == 0:  # Only add files (not folders)
                files.append(file_info)

    explore_folder("")  # Start from the root folder
    return files

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
        all_files = get_all_files(mega_session)
        if not all_files:
            return await message.reply("No files found in your Mega account.")

        renamed_count = 0
        for index, file_info in enumerate(all_files, start=1):
            try:
                # Extract file name and extension
                original_file_name = file_info["a"]["n"]
                file_extension = os.path.splitext(original_file_name)[1]
                new_file_name = f"{new_name}_{index}{file_extension}"

                # Rename the file
                mega_session.rename(file_info["h"], new_file_name)
                renamed_count += 1
                LOGGER.info(f"Renamed '{original_file_name}' to '{new_file_name}'")
            except Exception as e:
                LOGGER.error(f"Failed to rename file: {e}")
                continue

        await message.reply(f"Renaming complete. Total files renamed: {renamed_count}")
    except Exception as e:
        LOGGER.error(f"Error during renaming: {e}")
        await message.reply(f"Error: {e}")

# Run the bot
if __name__ == "__main__":
    LOGGER.info("Starting bot...")
    app.run()
