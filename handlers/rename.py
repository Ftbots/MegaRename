from pyrogram import filters
from pyrogram.types import Message
from mega import Mega
from config import MEGA_CREDENTIALS

def register_handlers(app):
    @app.on_message(filters.command("rename") & filters.private)
    async def rename(bot, message: Message):
        if not MEGA_CREDENTIALS["email"] or not MEGA_CREDENTIALS["password"]:
            await message.reply("You must be logged in to Mega. Use /login first.")
            return

        try:
            mega = Mega()
            m = mega.login(MEGA_CREDENTIALS["email"], MEGA_CREDENTIALS["password"])

            await message.reply("Send the file URL you want to rename.")
            file_url = (await bot.listen(message.chat.id)).text

            await message.reply("Send the new name for the file.")
            new_name = (await bot.listen(message.chat.id)).text

            file = m.find(file_url)
            m.rename(file, new_name)

            await message.reply(f"File renamed successfully to {new_name}!")
        except Exception as e:
            await message.reply(f"Rename failed: {str(e)}")