import asyncio
from pyrogram import Client, filters

async def listen(chat_id, app: Client, timeout=60):
    future = asyncio.get_event_loop().create_future()

    @app.on_message(filters.private & filters.chat(chat_id))
    async def handler(client, message):
        if not future.done():
            future.set_result(message)
        await app.remove_handler(handler)

    try:
        # Wait for user's input with a timeout
        return await asyncio.wait_for(future, timeout)
    except asyncio.TimeoutError:
        logging.error(f"Timeout: No response received within {timeout} seconds.")  # Log timeout error
        raise Exception("Timeout: No response received.")
