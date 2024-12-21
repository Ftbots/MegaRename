
import os
import re
import asyncio
import logging
import threading
import time
from datetime import datetime
from aiohttp import web
import pymongo

import aiohttp
from mega import Mega
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import BOT_TOKEN, API_ID, API_HASH, MEGA_CREDENTIALS, ADMIN_USER_ID, MONGO_URI, FORCE_JOIN_CHANNEL

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("pyrogram").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

# Initialize the bot and store start time
app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
app.mega = Mega()
app.mega_session = None
app.start_time = time.time()

# Initialize MongoDB connection
try:
    mongo_client = pymongo.MongoClient(MONGO_URI)
    db = mongo_client["your_database_name"]  # Replace "your_database_name" with your database name
    users_collection = db["users"]
except pymongo.errors.ConnectionFailure as e:
    LOGGER.error(f"MongoDB connection failed: {e}")
    exit(1)


async def add_user_to_db(user_id):
    try:
        users_collection.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)
    except Exception as e:
        LOGGER.error(f"Error adding user to MongoDB: {e}")


async def is_user_in_channel(user_id):
    try:
        member = await app.get_chat_member(chat_id=FORCE_JOIN_CHANNEL, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except UserNotParticipant:
        return False
    except Exception as e:
        LOGGER.error(f"Error checking channel membership: {e}")
        return False


async def enforce_channel_membership(client, message):
    if not await is_user_in_channel(message.from_user.id):
        invite_link = await app.create_chat_invite_link(chat_id=FORCE_JOIN_CHANNEL)
        join_button = InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url=invite_link.invite_link)]])
        await message.reply("Please join my channel first:", reply_markup=join_button, parse_mode="HTML")
        return True
    return False


async def start_process(client, message):
    await add_user_to_db(message.from_user.id)
    if await enforce_channel_membership(client, message):
        return
    await message.reply("Welcome to Mega Rename Bot!\nUse /login to log in to your Mega account.")


async def login_process(client, message):
    if await enforce_channel_membership(client, message):
        return
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
    if await enforce_channel_membership(client, message):
        return
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
        reply = await message.reply(f"Renaming files... 0/{total_files}")

        for file_id, file_info in files.items():
            try:
                old_name = file_info['a']['n'] if 'a' in file_info and 'n' in file_info['a'] else "Unknown Filename"
                base, ext = os.path.splitext(old_name)
                sanitized_new_name = re.sub(r'[\\/*?:"<>|]', "", new_base_name) + ext

                app.mega.rename((file_id, file_info), sanitized_new_name)
                renamed_count += 1
                await reply.edit(f"Renaming files... {renamed_count}/{total_files}")
                LOGGER.info(f"Renamed '{old_name}' to '{sanitized_new_name}'")
            except Exception as e:
                LOGGER.error(f"Failed to rename file: {e}")
                await reply.edit(f"Failed to rename file. Continuing...")

        await reply.edit(f"Rename process completed. {renamed_count} files renamed.")

    except Exception as e:
        LOGGER.error(f"Rename failed: {str(e)}")
        await message.reply(f"Rename failed: {str(e)}")


async def stats_process(client, message):
    if await enforce_channel_membership(client, message):
        return
    uptime_seconds = int(time.time() - app.start_time)
    uptime_days = uptime_seconds // (24 * 3600)
    uptime_hours = (uptime_seconds % (24 * 3600)) // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    await message.reply(f"Bot uptime: {uptime_days} days, {uptime_hours} hours, {uptime_minutes} minutes")


async def restart_process(client, message):
    if message.from_user.id == ADMIN_USER_ID:
        await message.reply("Restarting...")
        LOGGER.info("Bot restarting...")
        os._exit(0)
    else:
        await message.reply("You are not authorized to restart the bot.")


async def users_process(client, message):
    if message.from_user.id == ADMIN_USER_ID:
        try:
            total_users = users_collection.count_documents({})
            await message.reply(f"Total users: {total_users}")
        except Exception as e:
            LOGGER.error(f"Error getting user count: {str(e)}")
            await message.reply(f"Error getting user count: {str(e)}")
    else:
        await message.reply("You are not authorized to use this command.")


async def broadcast_process(client, message):
    if message.from_user.id == ADMIN_USER_ID:
        try:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                return await message.reply("Usage: /broadcast <message>")

            broadcast_message = args[1]
            user_ids = [user["user_id"] for user in users_collection.find({}, {"user_id": 1, "_id": 0})]

            sent_count = 0
            failed_count = 0

            async def send_to_user(user_id):
                nonlocal sent_count, failed_count
                try:
                    await app.send_message(chat_id=user_id, text=broadcast_message)
                    sent_count += 1
                except Exception as e:
                    LOGGER.error(f"Failed to send message to {user_id}: {e}")
                    failed_count += 1

            tasks = [send_to_user(user_id) for user_id in user_ids]
            await asyncio.gather(*tasks)

            await message.reply(f"Broadcast complete. Sent to {sent_count} users. Failed to send to {failed_count} users.")

        except Exception as e:
            LOGGER.error(f"Broadcast failed: {str(e)}")
            await message.reply(f"Broadcast failed: {str(e)}")
    else:
        await message.reply("You are not authorized to use this command.")


async def ping_process(client, message):
    if await enforce_channel_membership(client, message):
        return
    start_time = time.time()
    await message.reply("Pong!")
    end_time = time.time()
    ping_time = (end_time - start_time) * 1000
    await message.reply(f"Ping: {ping_time:.2f}ms")



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


threading.Thread(target=start_health_server, daemon=True).start()

# Command handlers
app.add_handler(MessageHandler(restart_process, filters.command("restart") & filters.user(ADMIN_USER_ID)))
app.add_handler(MessageHandler(login_process, filters.command("login")))
app.add_handler(MessageHandler(start_process, filters.command("start")))
app.add_handler(MessageHandler(rename_process, filters.command("rename")))
app.add_handler(MessageHandler(stats_process, filters.command("stats")))
app.add_handler(MessageHandler(users_process, filters.command("users") & filters.user(ADMIN_USER_ID)))
app.add_handler(MessageHandler(broadcast_process, filters.command("broadcast") & filters.user(ADMIN_USER_ID)))
app.add_handler(MessageHandler(ping_process, filters.command("ping")))


# Run the bot
LOGGER.info("Bot is running...")
app.run()
