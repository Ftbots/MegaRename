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
from pyrogram.filters import command, private
from pyrogram.handlers import MessageHandler
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
    db = mongo_client["your_database_name"]  # Replace "your_database_name" with your database name.
    users_collection = db["users"]
except pymongo.errors.ConnectionFailure as e:
    LOGGER.error(f"MongoDB connection failed: {e}")
    exit(1)

# Function to check channel membership
async def is_user_in_channel(user_id, channel_id):
    try:
        member = await app.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except Exception as e:
        LOGGER.error(f"Error checking channel membership: {e}")
        return False

# Simplified decorator
async def enforce_channel_membership(client, message):
    if not await is_user_in_channel(message.from_user.id, FORCE_JOIN_CHANNEL):
        await message.reply(
            f"Please join my channel first: [Join Channel](https://t.me/c/{str(FORCE_JOIN_CHANNEL)[3:]})",
            parse_mode="Markdown",
        )
        return True  # Signal to stop further command execution
    return False

# Command functions
async def start_process(client, message):
    await add_user_to_db(message.from_user.id)
    if await is_user_in_channel(message.from_user.id, FORCE_JOIN_CHANNEL):
        await message.reply("Welcome to Mega Rename Bot! Use /login to log in to your Mega account.")
    else:
        await message.reply(
            f"Please join my channel first: [Join Channel](https://t.me/c/{str(FORCE_JOIN_CHANNEL)[3:]})",
            parse_mode="Markdown",
        )

async def login_process(client, message):
    # Login process remains unchanged
    pass

async def rename_process(client, message):
    if await enforce_channel_membership(client, message):
        return
    # Rename process remains unchanged

async def stats_process(client, message):
    if await enforce_channel_membership(client, message):
        return
    # Stats process remains unchanged

async def restart_process(client, message):
    if message.from_user.id == ADMIN_USER_ID:
        await message.reply("Restarting...")
        LOGGER.info("Bot restarting...")
        os._exit(0)
    else:
        await message.reply("You are not authorized to restart the bot.")

async def users_process(client, message):
    # Users process remains unchanged
    pass

async def broadcast_process(client, message):
    # Broadcast process remains unchanged
    pass

async def ping_process(client, message):
    # Ping process remains unchanged
    pass

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

threading.Thread(target=start_health_server, daemon=True).start()

# Register handlers
app.add_handler(MessageHandler(start_process, filters.command("start")))
app.add_handler(MessageHandler(login_process, filters.command("login")))
app.add_handler(MessageHandler(rename_process, filters.command("rename")))
app.add_handler(MessageHandler(stats_process, filters.command("stats")))
app.add_handler(MessageHandler(users_process, filters.command("users") & filters.user(ADMIN_USER_ID)))
app.add_handler(MessageHandler(broadcast_process, filters.command("broadcast") & filters.user(ADMIN_USER_ID)))
app.add_handler(MessageHandler(ping_process, filters.command("ping")))
app.add_handler(MessageHandler(restart_process, filters.command("restart") & filters.user(ADMIN_USER_ID)))

# Run the bot
LOGGER.info("Bot is running...")
app.run()
