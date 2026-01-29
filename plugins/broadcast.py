import asyncio 
import time, datetime 
from database import db 
from config import Config
from pyrogram import Client, filters 
from pyrogram.errors import InputUserDeactivated, FloodWait, UserIsBlocked

@Client.on_message(filters.command("broadcast") & filters.user(Config.BOT_OWNER_ID) & filters.reply)
async def broadcast(bot, message):
    users = await db.get_all_users()
    b_msg = message.reply_to_message
    sts = await message.reply_text(
        text='<b>📢 Broadcasting your messages...</b>'
    )
    start_time = time.time()
    total_users, k = await db.total_users_bots_count()
    done = 0
    blocked = 0
    deleted = 0
    failed = 0 
    success = 0

    async for user in users:
        pti, sh = await broadcast_messages(int(user['id']), b_msg, bot.log)
        if pti:
            success += 1
            await asyncio.sleep(1) # Broadcast rate limit control
        elif pti == False:
            if sh == "Blocked":
                blocked += 1
            elif sh == "Deleted":
                deleted += 1
            elif sh == "Error":
                failed += 1
        
        done += 1
        if not done % 20:
            await sts.edit(f"<b>📢 Broadcast in progress:</b>\n\n<b>Total Users:</b> {total_users}\n<b>Completed:</b> {done} / {total_users}\n<b>Success:</b> {success}\n<b>Blocked:</b> {blocked}\n<b>Deleted:</b> {deleted}")    
    
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    await sts.edit(f"<b>✅ Broadcast Completed:</b>\n<b>Time Taken:</b> {time_taken}\n\n<b>Total Users:</b> {total_users}\n<b>Completed:</b> {done} / {total_users}\n<b>Success:</b> {success}\n<b>Blocked:</b> {blocked}\n<b>Deleted:</b> {deleted}")

async def broadcast_messages(user_id, message, log):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value) # Fixed e.x to e.value
        return await broadcast_messages(user_id, message, log)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        log.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        log.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except Exception as e:
        log.error(f"Broadcast Error for {user_id}: {e}")
        return False, "Error"
