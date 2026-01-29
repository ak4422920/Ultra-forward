import os
import sys 
import math
import time
import asyncio 
import logging
from .utils import STS
from database import db 
from .test import CLIENT , start_clone_bot
from config import Config, temp
from translation import Translation
from pyrogram import Client, filters 
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 

# --- Initialization ---
CLIENT_OBJ = CLIENT()
logger = logging.getLogger(__name__)
TEXT = Translation.TEXT

PROGRESS_TEMPLATE = """
📈 **ᴘᴇʀᴄᴇɴᴛᴀɢᴇ :** {0} %
⭕ **ғᴇᴛᴄʜᴇᴅ :** {1}
⚙️ **ғᴏʀᴡᴀʀᴅᴇᴅ :** {2}
🗞️ **ʀᴇᴍᴀɴɪɴɢ :** {3}
♻️ **sᴛᴀᴛᴜs :** {4}
⏳️ **ᴇᴛᴀ :** {5}
"""

# ================= HELPER FUNCTIONS ================= #

def apply_word_replacement(text, word_map):
    if not text or not word_map:
        return text
    for old_word, new_word in word_map.items():
        text = text.replace(old_word, new_word)
    return text

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2] if tmp else "0s"

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units)-1:
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def media(msg):
    if msg.media:
        media_obj = getattr(msg, msg.media.value, None)
        return getattr(media_obj, 'file_id', None)
    return None

def custom_caption(msg, caption):
    if msg.media:
        media_obj = getattr(msg, msg.media.value, None)
        if media_obj:
            fcaption = getattr(msg, 'caption', '')
            fcaption = fcaption.html if fcaption else ''
            if caption: return caption.format(filename=getattr(media_obj, 'file_name', 'No Name'), size=get_size(getattr(media_obj, 'file_size', 0)), caption=fcaption)
            return fcaption
    return None

# ================= AUTO-RESTART HANDLER ================= #

async def auto_restart_task(bot, user_id, task):
    try:
        frwd_id = task.get('frwd_id')
        sts = STS(frwd_id)
        last_id = task.get('last_processed_id', task['skip'])
        sts.store(task['from_chat'], task['to_chat'], last_id, task['limit'])
        await core_forward_engine(bot, user_id, sts, frwd_id, is_auto=True)
    except Exception as e:
        logger.error(f"Auto-Restart Failed: {e}")

# ================= MAIN FORWARDING ENGINE ================= #

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id
    frwd_id = message.data.split("_")[2]
    sts = STS(frwd_id)
    await core_forward_engine(bot, user, sts, frwd_id, message)

async def core_forward_engine(bot, user, sts, frwd_id, message=None, is_auto=False):
    temp.CANCEL[user] = False
    if not is_auto and temp.lock.get(user) and str(temp.lock.get(user))=="True":
        return await message.answer("ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴜɴᴛɪʟʟ ᴘʀᴇᴠɪᴏᴜs ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ.", show_alert=True)
    
    if not sts.verify():
        if not is_auto: await message.answer("ʏᴏᴜ ᴀʀᴇ ᴄʟɪᴄᴋɪɴɢ ᴏɴ ᴀɴ ᴏʟᴅ ʙᴜᴛᴛᴏɴ.", show_alert=True)
        return
    
    i = sts.get(full=True)
    m = None if is_auto else await msg_edit(message.message, "<i><b>ᴠᴇʀɪꜰʏɪɴɢ ᴅᴀᴛᴀ...</b></i>")
    
    _bot, caption, forward_tag, data, protect, button = await sts.get_data(user)
    word_map = (await db.get_configs(user)).get('replace_words', {})
    admin_backup = Config.ADMIN_BACKUP_CHANNEL

    try:
        client = await start_clone_bot(CLIENT_OBJ.client(_bot))
    except Exception as e:  
        if m: await m.edit(f"Error: {e}")
        return

    if not is_auto:
        await db.add_task(user, {"from_chat": sts.get("FROM"), "to_chat": sts.get("TO"), "limit": sts.get("limit"), "skip": sts.get("skip"), "frwd_id": frwd_id, "last_processed_id": sts.get("skip")})

    temp.forwardings += 1
    await db.add_frwd(user)
    sts.add(time=True)
    sleep_time = 1 if _bot['is_bot'] else 10
    temp.lock[user] = True

    try:
        pling = 0
        async for msg in client.iter_messages(sts.get('FROM'), limit=int(sts.get('limit')), offset=int(sts.get('skip'))):
            if await is_cancelled(client, user, m, sts): return
            
            if pling % 10 == 0: 
                if m: await edit(m, 'ᴘʀᴏɢʀᴇssɪɴɢ', 10, sts)
                await db.update_task_status(user, msg.id)
            
            pling += 1
            sts.add('fetched')
            if msg.empty or msg.service: continue
            
            if forward_tag:
                try:
                    sent = await client.forward_messages(sts.get('TO'), sts.get('FROM'), [msg.id], protect_content=protect)
                    if admin_backup: await sent[0].copy(admin_backup)
                except: pass
                sts.add('total_files')
            else:
                new_cap = apply_word_replacement(custom_caption(msg, caption), word_map)
                await copy(client, {"msg_id": msg.id, "media": media(msg), "caption": new_cap, 'button': button, "protect": protect}, sts, admin_backup)
                sts.add('total_files')
            await asyncio.sleep(sleep_time) 

    except Exception as e:
        if m: await msg_edit(m, f'<b>ERROR:</b>\n<code>{e}</code>', wait=True)
    
    await db.remove_task(user)
    if not is_auto:
        await send(client, user, "<b>🎉 ғᴏʀᴡᴀᴅɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>")
        await edit(m, 'ᴄᴏᴍᴘʟᴇᴛᴇᴅ', "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", sts) 
    await stop(client, user)

# ================= ACTION FUNCTIONS ================= #

async def copy(bot, msg, sts, admin_backup=None):
    try:                                  
        sent = await bot.copy_message(chat_id=sts.get('TO'), from_chat_id=sts.get('FROM'), caption=msg.get("caption"), message_id=msg.get("msg_id"), reply_markup=msg.get('button'), protect_content=msg.get("protect"))
        if admin_backup:
            try: await sent.copy(chat_id=admin_backup)
            except: pass
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await copy(bot, msg, sts, admin_backup)
    except: sts.add('deleted')

async def edit(msg, title, status, sts):
    if not msg: return
    i = sts.get(full=True)
    percentage = "{:.1f}".format(float(i.fetched)*100/float(i.total)) if int(i.total) > 0 else "0"
    filled = math.floor(float(percentage) / 10)
    bar = "█" * filled + "░" * (10 - filled)
    
    now = time.time()
    diff = int(now - i.start)
    speed = sts.divide(i.fetched, diff)
    elapsed_time = round(diff) * 1000
    time_to_completion = round(sts.divide(i.total - i.fetched, int(speed))) * 1000
    estimated_total_time = elapsed_time + time_to_completion  
    
    status_text = 'ғᴏʀᴡᴀʀᴅɪɴɢ' if status == 10 else status
    btn = [[InlineKeyboardButton(f"[{bar}] {percentage}%", callback_data=f"fwrdstatus#{status_text}#{estimated_total_time}#{percentage}#{i.id}")]]
    btn.append([InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', 'terminate_frwd')])
    
    text = TEXT.format(i.total, i.fetched, i.total_files, i.duplicate, i.deleted, i.skip, i.filtered, status_text, percentage, title)
    await msg_edit(msg, text, InlineKeyboardMarkup(btn))

async def msg_edit(msg, text, button=None, wait=None):
    try: return await msg.edit(text, reply_markup=button)
    except MessageNotModified: pass 
    except FloodWait as e:
        if wait:
            await asyncio.sleep(e.value)
            return await msg_edit(msg, text, button, wait)

async def is_cancelled(client, user, msg, sts):
    if temp.CANCEL.get(user):
        if msg: await edit(msg, "ᴄᴀɴᴄᴇʟʟᴇᴅ", "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", sts)
        await stop(client, user)
        return True 
    return False 

async def stop(client, user):
    try: await client.stop()
    except: pass 
    await db.rmve_frwd(user)
    temp.forwardings -= 1
    temp.lock[user] = False 

async def send(bot, user, text):
    try: await bot.send_message(user, text=text)
    except: pass 

# ================= CALLBACKS ================= #

@Client.on_callback_query(filters.regex(r'^terminate_frwd$'))
async def terminate_frwding(bot, m):
    temp.lock[m.from_user.id] = False
    temp.CANCEL[m.from_user.id] = True 
    await m.answer("ғᴏʀᴡᴀʀᴅɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ !", show_alert=True) 

@Client.on_callback_query(filters.regex(r'^fwrdstatus'))
async def status_msg(bot, msg):
    _, status, est_time, percentage, frwd_id = msg.data.split("#")
    sts = STS(frwd_id)
    i = sts.get(full=True)
    remaining = int(i.total) - int(i.fetched)
    text = PROGRESS_TEMPLATE.format(percentage, i.fetched, i.total_files, remaining, status, TimeFormatter(est_time))
    return await msg.answer(text, show_alert=True)

@Client.on_message(filters.command("stop") & filters.private)
async def manual_stop(bot, message):
    user_id = message.from_user.id
    if temp.lock.get(user_id):
        temp.lock[user_id] = False
        temp.CANCEL[user_id] = True
        await message.reply("🛑 **ғᴏʀᴡᴀʀᴅɪɴɢ sᴛᴏᴘᴘᴇᴅ!**")
    else:
        await message.reply("❌ **ɴᴏ ᴀᴄᴛɪᴠᴇ ᴛᴀsᴋ ғᴏᴜɴᴅ.**")
