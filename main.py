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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("pyrogram").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

async def handle_health_check(request):
    return web.Response(text="OK")

async def start_background_tasks(app):
    # Start the aiohttp server in a separate task
    server_task = asyncio.create_task(start_http_server(app))
    app['server_task'] = server_task

async def start_http_server(app):
    runner = web.AppRunner(app["http_app"])
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)  # Listen on all interfaces
    await site.start()

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

        tasks = []
        for file_id, file_info in files.items():
            try:
                old_name = file_info['a']['n'] if 'a' in file_info and 'n' in file_info['a'] else "Unknown Filename"
                base, ext = os.path.splitext(old_name)
                sanitized_new_name = re.sub(r'[\/*?:"<>|]', "", new_base_name) + ext
                task = asyncio.to_thread(app.mega.rename, ((file_id, file_info), sanitized_new_name))
                tasks.append(task)
            except (KeyError, TypeError) as e:
                LOGGER.error(f"Error accessing file information for ID {file_id}: {e}. Skipping this file.")
                await reply.edit_text(f"Error processing file with ID {file_id}. Skipping...\nContinuing with other files...\nPowered by NaughtyX")
            except Exception as e:
                LOGGER.error(f"Failed to prepare rename for '{old_name if 'old_name' in locals() else 'Unknown File'}': {e}")
                await reply.edit_text(f"Failed to prepare rename for '{old_name if 'old_name' in locals() else 'Unknown File'}': {e}\nContinuing with other files...\nPowered by NaughtyX")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                LOGGER.error(f"Rename failed: {result}")
            else:
                renamed_count += 1

        await reply.edit_text(f"Rename process completed. {renamed_count}/{total_files} files renamed.\nPowered by NaughtyX")
    except Exception as e:
        LOGGER.error(f"Rename failed: {str(e)}")
        await message.reply(f"Rename failed: {str(e)}")

async def main():
    http_app = web.Application()
    http_app.add_routes([web.get('/health', handle_health_check)])

    app_bot = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
    app_bot.mega = Mega()
    app_bot.mega_session = None
    app_bot["http_app"] = http_app

    app_bot.add_handler(MessageHandler(login_process, filters.command("login")))
    app_bot.add_handler(MessageHandler(start_process, filters.command("start")))
    app_bot.add_handler(MessageHandler(rename_process, filters.command("rename")))

    await app_bot.start()
    LOGGER.info("Bot is running...")

    await start_background_tasks(app_bot)
    await app_bot.idle()

if __name__ == "__main__":
    asyncio.run(main())
