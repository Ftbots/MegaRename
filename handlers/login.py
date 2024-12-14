from pyrogram import filters
from pyrogram.types import Message
from mega import Mega
from config import MEGA_CREDENTIALS

mega = Mega()

def register_handlers(app):
    @app.on_message(filters.command("login") & filters.private)
    async def login(bot, message: Message):
        await message.reply("Please send your Mega email.")
        email = (await bot.listen(message.chat.id)).text

        await message.reply("Now send your Mega password.")
        password = (await bot.listen(message.chat.id)).text

        try:
            mega.login(email, password)
            MEGA_CREDENTIALS["email"] = email
            MEGA_CREDENTIALS["password"] = password
            await message.reply("Mega login successful!")
        except Exception as e:
            await message.reply(f"Login failed: {str(e)}")

    @app.on_message(filters.command("logout") & filters.private)
    async def logout(bot, message: Message):
        MEGA_CREDENTIALS["email"] = None
        MEGA_CREDENTIALS["password"] = None
        await message.reply("You have been logged out of Mega.")