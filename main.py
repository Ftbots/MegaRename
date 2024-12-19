import os, re
import asyncio
import logging

from aiohttp import web
from mega import Mega

from pyrogram import Client
from pyrogram.filters import command, private, chat

from config import BOT_TOKEN, API_ID, API_HASH, MEGA_CREDENTIALS

# Enable logging for better error tracking
logging.basicConfig(level=logging.DEBUG)

# Initialize the bot
app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

@app.on_message(command("start") & private)
async def start(client, message):
    await message.reply("Welcome to Mega Rename Bot!\nUse /login to log in to your Mega account.")

@app.on_message(command("login") & private)
async def login(client, message):
    await message.reply("Please send your Mega email.")
    email_message = await listen(message.chat.id, app)
    email = email_message.text
    
    await message.reply("Now send your Mega password.")
    password_message = await listen(message.chat.id, app)
    password = password_message.text

    try:
        mega = Mega()
        mega.login(email, password)
        # Store mega instance for later use.  This is crucial
        app.mega = mega  
        await message.reply("Mega login successful!")
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        await message.reply(f"Login failed: {str(e)}")

@app.on_message(command("rename") & private)
async def rename(client, message):
    if not hasattr(app, 'mega') or not app.mega.is_logged_in:
        await message.reply("You must be logged in to Mega. Use /login first.")
        return
    try:
        await message.reply("Enter the rename pattern (e.g., 'oldname -> newname'):")
        pattern_message = await listen(message.chat.id, app)

        # Ensure pattern_message is valid
        if not pattern_message or not pattern_message.text:
            await message.reply("No pattern received. Rename process aborted.")
            return

        pattern_str = pattern_message.text.strip()

        # Improved pattern parsing using regex
        match = re.match(r"(.+)\s*->\s*(.+)", pattern_str)
        if not match:
            await message.reply("Invalid rename pattern. Use 'oldname -> newname'.")
            return

        old_pattern = match.group(1).strip()
        new_pattern = match.group(2).strip()

        # Retrieve files from Mega
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

async def listen(chat_id, app: Client, timeout=60):
    future = asyncio.get_event_loop().create_future()

    @app.on_message(filters.private & filters.chat(chat_id))
    async def handler(client, message):
        if not future.done():
            future.set_result(message)
        await app.remove_handler(handler)

    try:
        # Wait for user's input with a timeout
        return await asyncio.wait_for(future, timeout)
    except asyncio.TimeoutError:
        logging.error(f"Timeout: No response received within {timeout} seconds.")  # Log timeout error
        raise Exception("Timeout: No response received.")

async def health_check(request):
    return web.Response(text="OK", status=200)

def create_health_server():
    health_app = web.Application()
    health_app.router.add_get("/health", health_check)
    return health_app

async def main():
    health_server = create_health_server()
    runner = web.AppRunner(health_server)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=8080)
    await site.start()
    
    await app.start()
    print("Bot is running...")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

