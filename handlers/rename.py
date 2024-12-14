from pyrogram import filters
from pyrogram.types import Message
from mega import Mega
from utils import listen
import logging
import re

def register_handlers(app):
    @app.on_message(filters.command("rename") & filters.private)
    async def rename(bot, message: Message):
        if not hasattr(app, 'mega') or not app.mega.is_logged_in:
            await message.reply("You must be logged in to Mega. Use /login first.")
            return

        try:
            await message.reply("Enter the rename pattern (e.g., 'oldname -> newname'):")
            pattern_message = await listen(message.chat.id, app)
            pattern_str = pattern_message.text

            # Improved pattern parsing using regex
            match = re.match(r"(.+)\s*->\s*(.+)", pattern_str)
            if not match:
                await message.reply("Invalid rename pattern. Use 'oldname -> newname'.")
                return
            old_pattern = match.group(1)
            new_pattern = match.group(2)


            files = app.mega.get_files()
            renamed_count = 0
            for file in files:
                if re.search(old_pattern, file["name"]):
                    new_name = re.sub(old_pattern, new_pattern, file["name"])
                    try:
                        app.mega.rename(file["handle"], new_name)
                        renamed_count += 1
                        logging.info(f"Renamed '{file['name']}' to '{new_name}'")
                    except Exception as e:
                        logging.error(f"Failed to rename '{file['name']}': {e}")


            await message.reply(f"Rename process completed. {renamed_count} files renamed.")


        except Exception as e:
            logging.error(f"Rename failed: {str(e)}")
            await message.reply(f"Rename failed: {str(e)}")
