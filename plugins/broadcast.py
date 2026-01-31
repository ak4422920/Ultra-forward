import os
import time
import asyncio 
import logging 
from database import db
from config import Config
from translation import Translation
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("broadcast") & filters.user(Config.BOT_OWNER_ID))
async def broadcast(bot, message):
    if not message.reply_to_message:
        return await message.reply_text("<b>Reply to a message to broadcast it.</b>")
        
    msg = await message.reply_text("<b>Processing...</b>")
    
    users = await db.get_all_users()
    b_users = await db.get_banned()
    
    success = 0
    failed = 0
    blocked = 0
    
    start_time = time.time()
    
    async for user in users:
        user_id = user['id']
        
        # Skip banned users if necessary, or just broadcast to all non-banned
        if user_id in b_users:
            continue
            
        try:
            await message.reply_to_message.copy(chat_id=user_id)
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_to_message.copy(chat_id=user_id)
            success += 1
        except Exception as e:
            # Common errors: User blocked bot, User deleted account
            failed += 1
            blocked += 1
            
    total_time = time.time() - start_time
    await msg.edit(f"<b><u>BROADCAST COMPLETED</u></b>\n\n<b>Total Users:</b> <code>{success + failed}</code>\n<b>Success:</b> <code>{success}</code>\n<b>Failed:</b> <code>{failed}</code>\n<b>Time Taken:</b> <code>{total_time:.2f} seconds</code>")
