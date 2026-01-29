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

# ================= HELPER FUNCTIONS ================= #

def apply_word_replacement(text, word_map):
    if not text or not word_map: return text
    for old_word, new_word in word_map.items():
        text = text.replace(old_word, new_word)
    return text

# ================= MAIN FORWARDING ENGINE ================= #

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id
    frwd_id = message.data.split("_")[2]
    sts = STS(frwd_id)
    await core_forward_engine(bot, user, sts, frwd_id, message)

async def core_forward_engine(bot, user, sts, frwd_id, message=None, is_auto=False):
    temp.CANCEL[user] = False
    
    # 🔒 Problem #04: Lock Check
    if not is_auto and temp.lock.get(user):
        return await message.answer("ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴜɴᴛɪʟʟ ᴘʀᴇᴠɪᴏᴜs ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ.", show_alert=True)
    
    if not sts.verify():
        if not is_auto: await message.answer("ʏᴏᴜ ᴀʀᴇ ᴄʟɪᴄᴋɪɴɢ ᴏɴ ᴀɴ ᴏʟᴅ ʙᴜᴛᴛᴏɴ.", show_alert=True)
        return
    
    i = sts.get(full=True)
    m = None if is_auto else await msg_edit(message.message, "<i><b>ᴠᴇʀɪꜰʏɪɴɢ ᴅᴀᴛᴀ...</b></i>")
    
    _bot, caption, forward_tag, data, protect, button = await sts.get_data(user)
    configs = await db.get_configs(user)
    
    # Engine Settings
    word_map = configs.get('replace_words', {})
    size_limit = configs.get('file_size', 0) * 1024 * 1024 # Convert MB to Bytes
    banned_extensions = configs.get('extension', [])
    allowed_keywords = configs.get('keywords', [])
    admin_backup = Config.ADMIN_BACKUP_CHANNEL

    try:
        client = await start_clone_bot(CLIENT_OBJ.client(_bot))
        temp.lock[user] = True
        temp.IS_FRWD_CHAT.append(i.TO)
        sts.add(time=True)

        # 🎯 Problem #02 & #05: Smart Limit Calculation
        total_in_channel = int(sts.get('total'))
        skip_val = int(sts.get('skip'))
        actual_total = total_in_channel - skip_val
        
        user_limit = int(sts.get('limit'))
        f_limit = min(user_limit, actual_total) if user_limit > 0 else actual_total

        if f_limit <= 0:
            if m: await msg_edit(m, "❌ **Error:** Skip value total messages se zyada hai!")
            return

        pling = 0
        async for msg in client.iter_messages(sts.get('FROM'), limit=f_limit, offset=skip_val):
            if await is_cancelled(client, user, m, sts): return
            
            # 📈 Problem #01: Correct Progress Update
            if pling % 10 == 0: 
                if m: await edit(m, 'ᴘʀᴏɢʀᴇssɪɴɢ', 10, sts)
                await db.update_task_status(user, msg.id)
            
            pling += 1
            sts.add('fetched')
            if msg.empty or msg.service: continue

            # --- 🔍 SMART FILTERS (Size, Ext, Keywords) ---
            if msg.media:
                media_obj = getattr(msg, msg.media.value, None)
                if media_obj:
                    # 1. Size Limit Filter
                    if size_limit > 0 and getattr(media_obj, 'file_size', 0) > size_limit:
                        sts.add('filtered'); continue
                    
                    # 2. Extension Filter
                    file_name = getattr(media_obj, 'file_name', '').lower()
                    if banned_extensions and any(file_name.endswith(ext.lower()) for ext in banned_extensions):
                        sts.add('filtered'); continue
                    
                    # 3. Keyword Filter
                    if allowed_keywords and not any(word.lower() in file_name for word in allowed_keywords):
                        sts.add('filtered'); continue

            # --- FORWARDING LOGIC ---
            if forward_tag:
                try:
                    sent = await client.forward_messages(sts.get('TO'), sts.get('FROM'), [msg.id], protect_content=protect)
                    if admin_backup: await sent[0].copy(admin_backup)
                    sts.add('total_files')
                except: sts.add('deleted')
            else:
                new_cap = apply_word_replacement(custom_caption(msg, caption), word_map)
                await copy(client, {"msg_id": msg.id, "media": media(msg), "caption": new_cap, 'button': button, "protect": protect}, m, sts, admin_backup)
                sts.add('total_files')
            
            await asyncio.sleep(1 if _bot['is_bot'] else 5) 

    except Exception as e:
        logger.error(f"Engine Crash: {e}")
        if m: await msg_edit(m, f'<b>ERROR:</b>\n`{e}`', wait=True)
    
    finally:
        # 🔓 Problem #04: Bulletproof Unlock
        temp.lock[user] = False 
        if i.TO in temp.IS_FRWD_CHAT: temp.IS_FRWD_CHAT.remove(i.TO)
        await db.remove_task(user)
        if not is_auto:
            await send(client, user, "<b>🎉 ғᴏʀᴡᴀᴅɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>")
            await edit(m, 'ᴄᴏᴍᴘʟᴇᴛᴇᴅ', "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", sts) 
        await stop(client, user)

# ================= UI & ACTION HELPERS ================= #

async def edit(msg, title, status, sts):
    if not msg: return
    i = sts.get(full=True)
    
    # 📈 Formula: (Fetched / (Total - Skip)) * 100
    actual_total = int(i.total) - int(i.skip)
    if actual_total <= 0: actual_total = 1
    percentage = "{:.1f}".format(float(i.fetched) * 100 / actual_total)
    
    filled_blocks = math.floor(float(percentage) / 10)
    bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
    
    status_text = 'ғᴏʀᴡᴀʀᴅɪɴɢ' if status == 10 else status
    button = [[InlineKeyboardButton(f"[{bar}] {percentage}%", callback_data=f"none")]]
    
    if status in ["ᴄᴀɴᴄᴇʟʟᴇᴅ", "ᴄᴏᴍᴘʟᴇᴛᴇᴅ"]:
        button.append([InlineKeyboardButton('💠 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/Silicon_Official')])
    else:
        button.append([InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', 'terminate_frwd')])
    
    text = TEXT.format(i.total, i.fetched, i.total_files, i.duplicate, i.deleted, i.skip, i.filtered, status_text, percentage, title)
    await msg_edit(msg, text, InlineKeyboardMarkup(button))

async def copy(bot, msg, m, sts, admin_backup=None):
    try:                                  
        sent = await bot.copy_message(
            chat_id=sts.get('TO'), from_chat_id=sts.get('FROM'), 
            caption=msg.get("caption"), message_id=msg.get("msg_id"), 
            reply_markup=msg.get('button'), protect_content=msg.get("protect")
        )
        if admin_backup:
            try: await sent.copy(chat_id=admin_backup)
            except: pass
    except FloodWait as e:
        await asyncio.sleep(e.value); return await copy(bot, msg, m, sts, admin_backup)
    except: sts.add('deleted')

async def msg_edit(msg, text, button=None, wait=None):
    try: return await msg.edit(text, reply_markup=button)
    except MessageNotModified: pass 
    except FloodWait as e:
        if wait: await asyncio.sleep(e.value); return await msg_edit(msg, text, button, wait)

async def is_cancelled(client, user, msg, sts):
    if temp.CANCEL.get(user):
        if msg: await edit(msg, "ᴄᴀɴᴄᴇʟʟᴇᴅ", "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", sts)
        return True 
    return False 

async def stop(client, user):
    try: await client.stop()
    except: pass 
    await db.rmve_frwd(user)
    temp.lock[user] = False 

async def send(bot, user, text):
    try: await bot.send_message(user, text=text)
    except: pass 

def custom_caption(msg, caption):
    if msg.media:
        media_obj = getattr(msg, msg.media.value, None)
        if media_obj:
            fcaption = getattr(msg, 'caption', '')
            fcaption = fcaption.html if fcaption else ''
            if caption: 
                return caption.format(
                    filename=getattr(media_obj, 'file_name', 'No Name'), 
                    size=get_size(getattr(media_obj, 'file_size', 0)), 
                    caption=fcaption
                )
            return fcaption
    return None

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units)-1:
        i += 1; size /= 1024.0
    return "%.2f %s" % (size, units[i])

def media(msg):
    if msg.media:
        return getattr(getattr(msg, msg.media.value, None), 'file_id', None)
    return None

# ================= AUTO-RESUME WRAPPER ================= #

async def auto_restart_task(bot, user_id, task_data):
    """Ye function bot restart hone par task ko engine mein wapas bhejta hai."""
    # STS ko yahan import karna zaroori hai
    from .utils import STS
    frwd_id = task_data.get('frwd_id') 
    if frwd_id:
        sts = STS(frwd_id)
        # core_forward_engine ko is_auto=True ke saath chalana
        await core_forward_engine(bot, user_id, sts, frwd_id, is_auto=True)
