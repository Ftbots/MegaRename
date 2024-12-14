from pyrogram import filters
from pyrogram.types import Message
from mega import Mega
from config import MEGA_CREDENTIALS
from utils import listen  # Import the listen function

mega = Mega()

def register_handlers(app):
    @app.on_message(filters.command("login") & filters.private)
    async def login(bot, message: Message):
        await message.reply("Please send your Mega email.")

        # Use the custom listen function
        email_message = await listen(message.chat.id, app)
        email = email_message.text

        await message.reply("Now send your Mega password.")
        password_message = await listen(message.chat.id, app)
        password = password_message.text

        try:
            mega.login(email, password)
            MEGA_CREDENTIALS["email"] = email
            MEGA_CREDENTIALS["password"] = password
            await message.reply("Mega login successful!")
        except Exception as e:
            await message.reply(f"Login failed: {str(e)}")
