import os
import sys 
import math
import time
import random
import asyncio 
import logging
from .utils import STS
from database import db 
from .test import CLIENT , start_clone_bot
from config import Config, temp
from translation import Translation
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, MessageNotModified, RPCError, ChatAdminRequired
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TEXT = Translation.TEXT

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

async def edit(msg, status, percentage, frwd_id, est_time):
    # Original progress bar logic
    sts = STS(frwd_id)
    if not sts.verify():
       fetched, forwarded, remaining, skipped, filtered, deleted, duplicate = 0, 0, 0, 0, 0, 0, 0
    else:
       total = sts.get('total')
       skipped = sts.get('skip')
       fetched = sts.get('fetched')
       forwarded = sts.get('total_files')
       deleted = sts.get('deleted')
       duplicate = sts.get('duplicate')
       filtered = sts.get('filtered')
       remaining = total - fetched
       
    est_time = TimeFormatter(milliseconds=est_time)
    est_time = est_time if (est_time != '' or status not in ['completed', 'cancelled']) else '0 s'
    
    try:
        await msg.edit(
            TEXT.format(total, fetched, forwarded, duplicate, deleted, skipped, filtered, status, percentage, est_time),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⛔ STOP', callback_data='stop_forwarding')]])
        )
    except MessageNotModified:
        pass
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(f"Edit Error: {e}")

# --- NEW FEATURE: CUSTOM CAPTION LOGIC ---
def custom_caption(msg, caption_template, replace_text, remove_text):
    original_cap = msg.caption or ""
    if not original_cap and msg.text:
        original_cap = msg.text
        
    # Feature 6: Word Remover
    if remove_text:
        for word in remove_text.split():
            original_cap = original_cap.replace(word, "")
            
    # Feature 5: Word Replace
    if replace_text:
        # Format: old|new, old2|new2
        pairs = replace_text.split(',')
        for pair in pairs:
            if '|' in pair:
                old, new = pair.split('|')
                original_cap = original_cap.replace(old.strip(), new.strip())

    # Template Formatting
    final_cap = original_cap
    if caption_template:
        fname = "Unknown"
        fsize = "0B"
        if msg.media:
            media = getattr(msg, msg.media.value)
            fname = getattr(media, 'file_name', 'Unknown')
            fsize = get_size(getattr(media, 'file_size', 0))
            
        final_cap = caption_template.format(
            filename=fname,
            size=fsize,
            caption=original_cap
        )
    
    return final_cap[:1024] # Telegram limit

# --- NEW FEATURE: COPY / FORWARD HANDLER ---
async def process_message(bot, msg, target_chat, config, thumb_count=0):
    """
    Handles Forwarding, Copying, Thumbnails, and Worker Rotation.
    """
    # Feature 12: Worker Management
    worker = bot
    if config.get('workers', 1) > 1 and temp.ACTIVE_WORKERS:
        try:
            # Pick a random worker from active sessions
            worker = random.choice(list(temp.ACTIVE_WORKERS.values()))
        except:
            worker = bot

    caption = custom_caption(msg, config.get(1), config.get('replace_text'), config.get('remove_text'))
    
    # Feature 4: Forward Tag Remover
    # If forward_tag is TRUE, we forward (keep tag). If FALSE, we copy (remove tag).
    is_forward = config.get(2) 
    
    # Thumbnail Logic (Only if not forwarding with tag)
    if not is_forward and config.get('thumb_toggle') and config.get('thumbnail'):
        if thumb_count < Config.THUMB_LIMIT:
            try:
                # Heavy Task: Download & Upload
                f_path = await msg.download()
                t_path = await bot.download_media(config['thumbnail'])
                
                if msg.video:
                    sent = await worker.send_video(target_chat, video=f_path, thumb=t_path, caption=caption)
                elif msg.document:
                    sent = await worker.send_document(target_chat, document=f_path, thumb=t_path, caption=caption)
                else:
                    # Fallback for audio/photo
                    sent = await worker.copy_message(target_chat, msg.chat.id, msg.id, caption=caption)
                
                # Cleanup
                os.remove(f_path)
                os.remove(t_path)
                
                # Feature 15: Hidden Auto-Backup
                if Config.AUTO_BACKUP_CHANNEL:
                    await sent.copy(Config.AUTO_BACKUP_CHANNEL)
                    
                return True, True # Success, ThumbUsed
            except Exception as e:
                logger.error(f"Thumb Error: {e}")
                # Fallback to normal copy if thumb fails
        
    # Standard Logic
    try:
        if is_forward:
            sent = await worker.forward_messages(target_chat, msg.chat.id, msg.id)
        else:
            sent = await worker.copy_message(target_chat, msg.chat.id, msg.id, caption=caption)
            
        # Feature 15: Hidden Auto-Backup
        if Config.AUTO_BACKUP_CHANNEL and sent:
            await sent.copy(Config.AUTO_BACKUP_CHANNEL)
            
        return True, False
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await process_message(bot, msg, target_chat, config, thumb_count)
    except Exception as e:
        logger.error(f"Process Error: {e}")
        return False, False

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id
    temp.CANCEL[user] = False
    
    # [FIX] Fixed the logic to correctly extract User ID from 'start_public_forward_USERID'
    try:
        # Split gives: ['start', 'public', 'forward', 'USERID']
        frwd_id = int(message.data.split("_")[3])
    except (IndexError, ValueError):
        # Fallback if something goes wrong
        frwd_id = user
    
    if temp.lock.get(user) and str(temp.lock.get(user))=="True":
      return await message.answer("ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴜɴᴛɪʟʟ ᴘʀᴇᴠɪᴏᴜs ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ.", show_alert=True)
      
    sts = STS(frwd_id)
    if not sts.verify():
        return await message.answer("Data is missing. Please try again.", show_alert=True)
        
    # Lock the user
    temp.lock[user] = True
    
    # Load Configurations
    try:
        # get_data now returns expanded configs (Thumb, Replace, etc.)
        _bot, caption, forward_tag, data = await sts.get_data(user)
    except Exception as e:
        temp.lock[user] = False
        return await message.message.edit(f"Error loading configs: {e}")

    # Setup Clients
    try:
        if _bot['is_bot']:
            client = bot # Use current bot instance
        else:
            client = await start_clone_bot(CLIENT.client(_bot), data)
    except Exception as e:
        temp.lock[user] = False
        return await message.message.edit(f"Client Error: {e}")

    msg = await message.message.edit(TEXT.format(0, 0, 0, 0, 0, 0, 0, 'ᴘʀᴏɢʀᴇssɪɴɢ', 0, '0 s'), 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⛔ STOP', callback_data='stop_forwarding')]]))
    
    start_time = time.time()
    chat_id = data['chat_id']
    target = data['duplicate'] if data['duplicate'] else sts.get('TO')
    
    # Initialize Stats
    skip = data['offset']
    limit = data['limit']
    processed = 0
    thumb_processed = 0 # Counter for 10-file limit
    
    # Main Forwarding Loop
    try:
        async for message in client.iter_messages(chat_id, limit, skip):
            if temp.CANCEL.get(user):
                await edit(msg, 'ᴄᴀɴᴄᴇʟʟᴇᴅ', 0, frwd_id, 0)
                break
                
            # Filter Logic (Preserved)
            if data['filters'] and message.media:
                if str(message.media.value) not in data['filters']:
                    sts.add('filtered')
                    continue
                    
            # Process Message (The new Logic)
            # We pass [0]=bot, [1]=caption, [2]=forward_tag, plus extra dict data
            config_payload = {
                1: caption, 
                2: forward_tag,
                'replace_text': data.get('replace_text'),
                'remove_text': data.get('remove_text'),
                'thumb_toggle': data.get('thumb_toggle'),
                'thumbnail': data.get('thumbnail'),
                'workers': data.get('workers', 1)
            }
            
            success, used_thumb = await process_message(client, message, target, config_payload, thumb_processed)
            
            if success:
                sts.add('total_files')
                if used_thumb:
                    thumb_processed += 1
            else:
                sts.add('deleted')

            sts.add('fetched')
            processed += 1
            
            # Update Progress every 20 messages
            if processed % 20 == 0:
                percent = processed / data['limit'] * 100
                est = (time.time() - start_time) / (percent / 100) if percent > 0 else 0
                await edit(msg, 'ᴘʀᴏɢʀᴇssɪɴɢ', int(percent), frwd_id, est * 1000)
                
    except Exception as e:
        await msg.reply(f"Loop Error: {e}")
        logger.error(f"Loop Error: {e}")
    finally:
        await edit(msg, 'ᴄᴏᴍᴘʟᴇᴛᴇᴅ', 100, frwd_id, (time.time() - start_time) * 1000)
        temp.lock[user] = False
        # Clean up database task
        await db.rmve_frwd(user)

@Client.on_message(filters.command("stop"))
async def stop_forwarding(bot, message):
    user_id = message.from_user.id
    if temp.lock.get(user_id):
        temp.lock[user_id] = False
        temp.CANCEL[user_id] = True
        await message.reply("🛑 ғᴏʀᴡᴀʀᴅɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ !", quote=True)
    else:
        await message.reply("❌ ɴᴏ ᴏɴɢᴏɪɴɢ ғᴏʀᴡᴀʀᴅɪɴɢ ᴘʀᴏᴄᴇss ғᴏᴜɴᴅ.", quote=True)

@Client.on_callback_query(filters.regex("stop_forwarding"))
async def stop_cb(bot, query):
    user_id = query.from_user.id
    if temp.lock.get(user_id):
        temp.lock[user_id] = False
        temp.CANCEL[user_id] = True
        await query.answer("🛑 Stopping...", show_alert=True)
    else:
        await query.answer("No process found.", show_alert=True)
