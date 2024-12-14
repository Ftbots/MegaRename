from pyrogram import filters
from pyrogram.types import Message

def register_handlers(app):
    @app.on_message(filters.command("start") & filters.private)
    async def start(bot, message: Message):
        await message.reply("Welcome to Mega Rename Bot!\nUse /login to log in to your Mega account.")