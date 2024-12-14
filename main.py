import asyncio
from aiohttp import web
from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH
from handlers import start, login, rename

# Initialize the bot
app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Add handlers
start.register_handlers(app)
login.register_handlers(app)
rename.register_handlers(app)

# Health check route
async def health_check(request):
    return web.Response(text="OK", status=200)

# Create the health server
def create_health_server():
    health_app = web.Application()
    health_app.router.add_get("/health", health_check)
    return health_app

# Main asynchronous function to start the server and bot
async def main():
    # Start the health server
    health_server = create_health_server()
    runner = web.AppRunner(health_server)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=8080)
    await site.start()

    # Start the Pyrogram bot
    await app.start()
    print("Bot is running...")

    # Keep the event loop running to maintain bot operations
    await asyncio.Event().wait()

# Entry point for the program
if __name__ == "__main__":
    asyncio.run(main())
