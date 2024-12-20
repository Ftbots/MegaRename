import os
import re
import asyncio
import logging
from aiohttp import web
from mega import Mega
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from config import BOT_TOKEN, API_ID, API_HASH

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("pyrogram").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
app.mega = Mega()
app.mega_session = None

async def start_process(client, message):
    await message.reply("Welcome to Mega Rename Bot!\nUse /login to log in to your Mega account.")

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
        reply = await message.reply(f"Renaming files... 0/{total_files}")

        renamed_count = 0
        for file_id, file_info in files.items():
            try:
                old_name = file_info['a']['n'] if 'a' in file_info and 'n' in file_info['a'] else "Unknown Filename"
                base, ext = os.path.splitext(old_name)
                sanitized_new_name = re.sub(r'[\/*?:"<>|]', "", new_base_name) + ext

                await asyncio.to_thread(app.mega.rename, ((file_id, file_info), sanitized_new_name))

                renamed_count += 1
                await reply.edit_text(f"Renaming files... {renamed_count}/{total_files}\nPowered by NaughtyX")
            except (KeyError, TypeError) as e:
                LOGGER.error(f"Error accessing file information for ID {file_id}: {e}. Skipping this file.")
            except Exception as e:
                LOGGER.error(f"Failed to rename '{old_name}': {e}")

        await reply.edit_text(f"Rename process completed. {renamed_count}/{total_files} files renamed.\nPowered by NaughtyX")

    except Exception as e:
        LOGGER.error(f"Rename failed: {str(e)}")
        await message.reply(f"Rename failed: {str(e)}")

async def handle_health_check(request):
    return web.Response(text="OK")

async def main():
    web_app = web.Application()
    web_app.add_routes([web.get('/health', handle_health_check)])
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

    await app.start()
    await app.idle()
    await runner.cleanup()

if __name__ == "__main__":
    app.add_handler(MessageHandler(start_process, filters.command("start")))
    app.add_handler(MessageHandler(login_process, filters.command("login")))
    app.add_handler(MessageHandler(rename_process, filters.command("rename")))
    asyncio.run(main())
