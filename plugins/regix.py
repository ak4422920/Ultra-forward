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

# ================= AUTO-RESUME WRAPPER ================= #
async def auto_restart_task(bot, user_id, task_data):
    """Bot restart hone par task ko engine mein resume karta hai."""
    from .utils import STS
    frwd_id = task_data.get('frwd_id') 
    if frwd_id:
        sts = STS(frwd_id)
        # is_auto=True lock bypass karne ke liye
        await core_forward_engine(bot, user_id, sts, frwd_id, is_auto=True)

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
    
    # 🔒 Lock Check: Taaki ek saath do task na chalein
    if not is_auto and temp.lock.get(user):
        return await message.answer("ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴜɴᴛɪʟʟ ᴘʀᴇᴠɪᴏᴜs ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ.", show_alert=True)
    
    if not sts.verify(): return
    
    i = sts.get(full=True)
    m = None if is_auto else await msg_edit(message.message, "<i><b>ᴠᴇʀɪꜰʏɪɴɢ ᴅᴀᴛᴀ...</b></i>")
    
    # duplicate settings fetch karna
    _bot, caption, forward_tag, data, protect, button = await sts.get_data(user)
    configs = await db.get_configs(user)
    
    word_map = configs.get('replace_words', {})
    size_limit = configs.get('file_size', 0) * 1024 * 1024 
    banned_extensions = configs.get('extension', [])
    allowed_keywords = configs.get('keywords', [])
    admin_backup = Config.ADMIN_BACKUP_CHANNEL

    try:
        client = await start_clone_bot(CLIENT_OBJ.client(_bot))
        temp.lock[user] = True
        sts.add(time=True)

        # 🎯 Smart Limit: LIMIT REMOVED, ab total - skip chalega
        total_in_channel = int(sts.get('total'))
        skip_val = int(sts.get('skip'))
        f_limit = total_in_channel - skip_val 

        if f_limit <= 0:
            if m: await msg_edit(m, "❌ **Error:** Skip value messages se zyada hai!")
            return

        # Duplicate check uri
        db_uri = data.get('skip_duplicate') 

        pling = 0
        async for msg in client.iter_messages(sts.get('FROM'), limit=f_limit, offset=skip_val):
            if temp.CANCEL.get(user): break
            
            # Progress Update: (Fetched / (Total - Skip))
            if pling % 10 == 0 and m: 
                await edit(m, 'ᴘʀᴏɢʀᴇssɪɴɢ', 10, sts)
                await db.update_task_status(user, msg.id)
            
            pling += 1
            sts.add('fetched')
            if msg.empty or msg.service: continue

            # --- 🛡️ DUPLICATE DETECTION ---
            if db_uri and msg.media:
                file_unique_id = getattr(getattr(msg, msg.media.value, None), 'file_unique_id', None)
                if file_unique_id and await db.is_duplicate(db_uri[0], db_uri[1], file_unique_id):
                    sts.add('duplicate') #
                    continue

            # --- 🔍 SMART FILTERS ---
            if msg.media:
                media_obj = getattr(msg, msg.media.value, None)
                if media_obj:
                    if size_limit > 0 and getattr(media_obj, 'file_size', 0) > size_limit:
                        sts.add('filtered'); continue
                    
                    file_name = getattr(media_obj, 'file_name', '').lower()
                    if banned_extensions and any(file_name.endswith(ext.lower()) for ext in banned_extensions):
                        sts.add('filtered'); continue
                    
                    if allowed_keywords and not any(word.lower() in file_name for word in allowed_keywords):
                        sts.add('filtered'); continue

            # --- FORWARDING LOGIC ---
            try:
                if forward_tag:
                    sent = await client.forward_messages(sts.get('TO'), sts.get('FROM'), [msg.id], protect_content=protect)
                    if admin_backup: await sent[0].copy(admin_backup)
                else:
                    new_cap = apply_word_replacement(custom_caption(msg, caption), word_map)
                    await copy(client, {"msg_id": msg.id, "media": media(msg), "caption": new_cap, 'button': button, "protect": protect}, m, sts, admin_backup)
                
                sts.add('total_files')
                # Fingerprint save karna
                if db_uri and msg.media:
                    await db.save_fingerprint(db_uri[0], db_uri[1], file_unique_id)

            except Exception:
                sts.add('deleted')
            
            await asyncio.sleep(1.5 if _bot['is_bot'] else 5) 

    except Exception as e:
        if m: await msg_edit(m, f'<b>ERROR:</b>\n`{e}`', wait=True)
    
    finally:
        # 🔓 Lock release ensure karna
        temp.lock[user] = False 
        await db.remove_task(user)
        if not is_auto and m:
            await edit(m, 'ᴄᴏᴍᴘʟᴇᴛᴇᴅ', "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", sts) 
        await client.stop()

# ================= UI & ACTION HELPERS ================= #
async def edit(msg, title, status, sts):
    if not msg: return
    i = sts.get(full=True)
    actual_total = int(i.total) - int(i.skip)
    if actual_total <= 0: actual_total = 1
    percentage = "{:.1f}".format(float(i.fetched) * 100 / actual_total)
    
    filled_blocks = math.floor(float(percentage) / 10)
    bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
    
    status_text = 'ғᴏʀᴡᴀʀᴅɪɴɢ' if status == 10 else status
    button = [[InlineKeyboardButton(f"[{bar}] {percentage}%", callback_data="none")]]
    
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
