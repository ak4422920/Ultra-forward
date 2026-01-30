import os
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

# ================= HELPERS ================= #
def apply_word_replacement(text, word_map):
    if not text or not word_map: return text
    for old_word, new_word in word_map.items():
        text = text.replace(old_word, new_word)
    return text

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units)-1:
        i += 1; size /= 1024.0
    return "%.2f %s" % (size, units[i])

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

async def auto_restart_task(bot, user_id, task_data):
    frwd_id = task_data.get('frwd_id') 
    if frwd_id:
        sts = STS(frwd_id)
        await core_forward_engine(bot, user_id, sts, frwd_id, is_auto=True)

# ================= STOP HANDLER ================= #
@Client.on_message(filters.command('stop') & filters.private)
async def stop_handler(bot, message):
    user_id = message.from_user.id
    temp.CANCEL[user_id] = True
    temp.lock[user_id] = False
    await message.reply("<b>🛑 Task Stopped:</b> Lock reset ho gaya hai.")

# ================= COMMAND HANDLER ================= #
@Client.on_message(filters.command('forward') & filters.private)
async def forward_handler(bot, message):
    user_id = message.from_user.id
    if temp.lock.get(user_id):
        return await message.reply("<b>❌ Error:</b> Pehle se ek task chal raha hai.")

    # Source parsing
    source = await bot.ask(user_id, Translation.FROM_MSG)
    if source.text == "/cancel": return await message.reply(Translation.CANCEL)
    
    chat_id = None
    if source.forward_from_chat: chat_id = source.forward_from_chat.id
    elif source.text:
        if "t.me/c/" in source.text: chat_id = int("-100" + source.text.split("/")[-2])
        else:
            try: chat_id = source.text.split("/")[-2]
            except: return await message.reply("<b>❌ Error:</b> Invalid Link!")

    # Multi-Target parsing
    target = await bot.ask(user_id, Translation.TO_MSG)
    if target.text == "/cancel": return await message.reply(Translation.CANCEL)
    target_ids = target.text.replace(" ", "")

    # Skip parsing
    skip = await bot.ask(user_id, Translation.SKIP_MSG)
    if skip.text == "/cancel": return await message.reply(Translation.CANCEL)
    skip_val = int(skip.text) if skip.text.isdigit() else 0

    frwd_id = f"{user_id}_{int(time.time())}"
    sts = STS(frwd_id).store(chat_id, target_ids, skip_val, 0)
    
    btn = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 START FORWARD", callback_data=f"start_public_{frwd_id}")]])
    await message.reply("<b>✅ Setup Complete!</b> Click niche karein start karne ke liye.", reply_markup=btn)

# ================= MAIN FORWARDING ENGINE ================= #


@Client.on_callback_query(filters.regex(r'^start_public_'))
async def pub_(bot, query):
    user = query.from_user.id
    frwd_id = query.data.split("_")[2]
    sts = STS(frwd_id)
    await core_forward_engine(bot, user, sts, frwd_id, query)

async def core_forward_engine(bot, user, sts, frwd_id, query=None, is_auto=False):
    temp.CANCEL[user] = False
    if not is_auto and temp.lock.get(user): return
    if not sts.verify(): return
    
    _bot, caption, forward_tag, data, protect, button = await sts.get_data(user)
    configs = await db.get_configs(user)
    word_map = configs.get('replace_words', {})
    thumb_path = configs.get('thumbnail')
    admin_backup = Config.AUTO_BACKUP_CHANNEL
    target_list = str(sts.get('TO')).split(",")

    try:
        client = await start_clone_bot(CLIENT_OBJ.client(_bot))
        temp.lock[user] = True
        
        # Smart total message fetching
        total_msgs = await client.get_chat_history_count(sts.get('FROM'))
        sts.store(sts.get('FROM'), sts.get('TO'), sts.get('skip'), total_msgs)
        
        f_limit = total_msgs - int(sts.get('skip'))
        if thumb_path: f_limit = min(f_limit, Config.THUMB_LIMIT) # VPS Safety Lock

        await db.add_task(user, {'frwd_id': frwd_id, 'status': 'running'})
        m = query.message if not is_auto else await bot.send_message(user, "<b>♻️ Resuming...</b>")
        
        pling = 0
        async for msg in client.get_chat_history(sts.get('FROM'), limit=f_limit, offset_id=int(sts.get('skip'))):
            if temp.CANCEL.get(user): break
            if pling % 5 == 0: 
                await edit(m, 'ғᴏʀᴡᴀʀᴅɪɴɢ', 10, sts)
                await db.update_task_status(user, msg.id)
            
            pling += 1; sts.add('fetched')
            if msg.empty or msg.service: continue

            # Duplicate Check
            if msg.media and configs.get('duplicate'):
                file_id = getattr(getattr(msg, msg.media.value), 'file_unique_id', None)
                if await db.is_duplicate(user, file_id):
                    sts.add('duplicate'); continue

            new_cap = apply_word_replacement(custom_caption(msg, caption), word_map)

            # --- TARGET LOOP (1 TO 5) ---
            
            for target in target_list:
                try:
                    t_id = int(target)
                    # PATH A: Thumbnail Re-upload (Slow but Custom)
                    if thumb_path and msg.media:
                        path = await client.download_media(msg)
                        sent = await client.send_document(t_id, document=path, thumb=thumb_path, caption=new_cap, protect_content=protect)
                        if os.path.exists(path): os.remove(path)
                    # PATH B: Fast Copy/Forward (Instant)
                    else:
                        if forward_tag: sent = await client.forward_messages(t_id, sts.get('FROM'), [msg.id])
                        else: sent = await client.copy_message(t_id, sts.get('FROM'), msg.id, caption=new_cap, protect_content=protect, reply_markup=button)
                    
                    if admin_backup: 
                        backup_msg = sent[0] if isinstance(sent, list) else sent
                        await backup_msg.copy(admin_backup)
                except Exception as e: logger.error(f"Target Error: {e}")
            
            sts.add('total_files')
            if msg.media and configs.get('duplicate'): await db.save_fingerprint(user, file_id)
            await asyncio.sleep(1.5) # Fast but safe

    except Exception as e: logger.error(f"Global Engine Error: {e}")
    finally:
        temp.lock[user] = False 
        await db.remove_task(user)
        await edit(m, 'ᴄᴏᴍᴘʟᴇᴛᴇᴅ', "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", sts)
        if client.is_connected: await client.stop()

async def edit(msg, title, status, sts):
    if not msg: return
    i = sts.get(full=True)
    actual = int(i.total) - int(i.skip)
    percentage = "{:.1f}".format(float(i.fetched) * 100 / (actual if actual > 0 else 1))
    filled = math.floor(float(percentage) / 10)
    bar = "█" * filled + "░" * (10 - filled)
    
    button = [[InlineKeyboardButton(f"[{bar}] {percentage}%", callback_data="none")]]
    if status == "ᴄᴏᴍᴘʟᴇᴛᴇᴅ": button.append([InlineKeyboardButton('💠 ᴜᴘᴅᴀᴛᴇ', url=Config.FORCE_SUB_CHANNEL)])
    else: button.append([InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', callback_data='terminate_frwd')])
    
    try:
        await msg.edit(TEXT.format(i.total, i.fetched, i.total_files, i.duplicate, "0", i.skip, "0", status, percentage, title), reply_markup=InlineKeyboardMarkup(button))
    except MessageNotModified: pass
