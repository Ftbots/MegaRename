from pyrogram import filters
from pyrogram.types import Message

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply("Welcome to Mega Rename Bot!\nUse /login to log in to your Mega account.")
