#NaughtyX

import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import FORCE_SUB_CHANNEL, ADMINS
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait


async def is_subscribed(filter, client, update):
    if not FORCE_SUB_CHANNEL:
        return True  # Force-subscription is disabled
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True  # Admins are exempt
    try:
        member = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
            return False
        else:
            return True
    except UserNotParticipant:
        return False
    except Exception as e:  #Adding a broad exception handler
        print(f"Error checking subscription: {e}")
        return False #Return False if any error occurs.

subscribed = filters.create(is_subscribed)
