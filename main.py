import os
from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH
from handlers import start, login, rename

# Initialize the bot
app = Client("mega_rename_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Add handlers
start.register_handlers(app)
login.register_handlers(app)
rename.register_handlers(app)

if __name__ == "__main__":
    # Run the app on port specified by Koyeb
    port = int(os.environ.get("PORT", 8000))  # Default to 8000 if not set
    app.run(host="0.0.0.0", port=port)
