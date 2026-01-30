import asyncio 
import time, datetime 
import logging
from database import db 
from config import Config
from pyrogram import Client, filters 
from pyrogram.errors import InputUserDeactivated, FloodWait, UserIsBlocked

# Standard Logger setup
logger = logging.getLogger(__name__)

@Client.on_message(filters.command("broadcast") & filters.user(Config.BOT_OWNER_ID) & filters.reply)
async def broadcast(bot, message):
    users = await db.get_all_users()
    b_msg = message.reply_to_message
    
    sts = await message.reply_text(
        text='<b>📢 ɪɴɪᴛɪᴀᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ...</b>\n<i>Scanning database users.</i>'
    )
    
    start_time = time.time()
    total_users, _ = await db.total_users_bots_count()
    done = 0
    blocked = 0
    deleted = 0
    failed = 0 
    success = 0

    # Engine for sequential broadcasting to avoid Telegram spam filters 
    
    
    async for user in users:
        u_id = int(user['id'])
        
        # Broadcast logic
        result, status = await broadcast_messages(u_id, b_msg)
        
        if result:
            success += 1
        else:
            if status == "Blocked":
                blocked += 1
            elif status == "Deleted":
                deleted += 1
            else:
                failed += 1
        
        done += 1
        
        # Real-time UI Update every 20 users
        if done % 20 == 0:
            try:
                await sts.edit(
                    f"<b>📢 ʙʀᴏᴀᴅᴄᴀsᴛ ɪɴ ᴘʀᴏɢʀᴇss...</b>\n\n"
                    f"• <b>Total Users:</b> <code>{total_users}</code>\n"
                    f"• <b>Processed:</b> <code>{done}</code>\n"
                    f"• <b>Success:</b> ✅ <code>{success}</code>\n"
                    f"• <b>Blocked:</b> 🚫 <code>{blocked}</code>\n"
                    f"• <b>Deleted:</b> 🗑️ <code>{deleted}</code>"
                )
            except:
                pass
        
        # Anti-Spam delay (Safety first)
        await asyncio.sleep(0.5)
    
    time_taken = str(datetime.timedelta(seconds=int(time.time()-start_time)))
    
    final_text = (
        f"<b>✅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!</b>\n\n"
        f"<b>⏱️ Time Taken:</b> <code>{time_taken}</code>\n"
        f"<b>📊 Final Stats:</b>\n"
        f"• Success: <code>{success}</code>\n"
        f"• Blocked: <code>{blocked}</code>\n"
        f"• Deleted: <code>{deleted}</code>\n"
        f"• Failed: <code>{failed}</code>\n\n"
        f"<i>Database automatically cleaned.</i>"
    )
    
    await sts.edit(final_text)

async def broadcast_messages(user_id, message):
    try:
        # copy_message is best as it doesn't show "forwarded from" tag
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        # User deleted account - Remove from DB
        await db.delete_user(user_id)
        return False, "Deleted"
    except UserIsBlocked:
        # User blocked bot - Optional: keep in DB or remove. 
        # Removing keeps DB clean for next broadcast.
        await db.delete_user(user_id) 
        return False, "Blocked"
    except Exception as e:
        logger.error(f"Broadcast Error for {user_id}: {e}")
        return False, "Error"
