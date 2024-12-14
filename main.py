import asyncio
import logging
from aiohttp import web
from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH
from handlers import start, login, rename

# Enable logging for better error tracking
logging.basicConfig(level=logging.DEBUG)

# Initialize the bot
app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Add handlers
start.register_handlers(app)
login.register_handlers(app)
rename.register_handlers(app)

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
