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

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TEXT = Translation.TEXT

# ================= HELPER FUNCTIONS ================= #

def apply_word_replacement(text, word_map):
    """Point #1: Har user ke specific keywords ko change ya remove karta hai."""
    if not text or not word_map:
        return text
    for old_word, new_word in word_map.items():
        text = text.replace(old_word, new_word)
    return text

# ================= AUTO-RESTART HANDLER ================= #

async def auto_restart_task(bot, user_id, task):
    """Point #4 & #6: Ye function bot.py call karega restart ke waqt."""
    try:
        frwd_id = task.get('frwd_id')
        sts = STS(frwd_id)
        # STS object ko wapas load karna
        sts.store(task['from_chat'], task['to_chat'], task['skip'], task['limit'])
        
        # Core logic ko automatic mode mein trigger karna
        await core_forward_engine(bot, user_id, sts, frwd_id, is_auto=True)
    except Exception as e:
        logger.error(f"Auto-Restart Failed for {user_id}: {e}")

# ================= MAIN FORWARDING ENGINE ================= #

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id
    frwd_id = message.data.split("_")[2]
    sts = STS(frwd_id)
    # Manual trigger
    await core_forward_engine(bot, user, sts, frwd_id, message)

async def core_forward_engine(bot, user, sts, frwd_id, message=None, is_auto=False):
    """Main Engine: Manual aur Auto-Restart dono isi se chalenge."""
    temp.CANCEL[user] = False
    
    # Lock Check (Sirf manual start ke liye)
    if not is_auto and temp.lock.get(user) and str(temp.lock.get(user))=="True":
      return await message.answer("ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴜɴᴛɪʟʟ ᴘʀᴇᴠɪᴏᴜs ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ.", show_alert=True)
    
    if not sts.verify():
      if not is_auto: await message.answer("ʏᴏᴜ ᴀʀᴇ ᴄʟɪᴄᴋɪɴɢ ᴏɴ ᴀɴ ᴏʟᴅ ʙᴜᴛᴛᴏɴ.", show_alert=True)
      return
    
    i = sts.get(full=True)
    if not is_auto and i.TO in temp.IS_FRWD_CHAT:
      return await message.answer("ɪɴ ᴛᴀʀɢᴇᴛ ᴄʜᴀᴛ ᴛᴀsᴋ ɪs ɪɴ ᴘʀᴏɢʀᴇss.", show_alert=True)
    
    # Progress Notify
    m = None
    if not is_auto:
        m = await msg_edit(message.message, "<i><b>ᴠᴇ rɪꜰʏɪɴɢ ᴅᴀᴛᴀ...</b></i>")
    
    _bot, caption, forward_tag, data, protect, button = await sts.get_data(user)
    configs = await db.get_configs(user)
    word_map = configs.get('replace_words', {})
    
    # Global Admin Backup Channel from Config
    admin_backup = Config.ADMIN_BACKUP_CHANNEL

    if not _bot:
        if m: await msg_edit(m, "<code>ᴀᴅᴅ ᴀ ʙᴏᴛ ɪɴ /settings ғɪʀsᴛ</code>", wait=True)
        return
    
    try:
      client = await start_clone_bot(CLIENT.client(_bot))
    except Exception as e:  
      if m: await m.edit(e)
      return

    # Task tracking save karna (Point #4)
    if not is_auto:
        task_data = {
            "from_chat": sts.get("FROM"),
            "to_chat": sts.get("TO"),
            "limit": sts.get("limit"),
            "skip": sts.get("skip"),
            "frwd_id": frwd_id
        }
        await db.add_task(user, task_data)

    temp.forwardings += 1
    await db.add_frwd(user)
    sts.add(time=True)
    sleep = 1 if _bot['is_bot'] else 10
    temp.IS_FRWD_CHAT.append(i.TO)
    temp.lock[user] = True

    try:
      MSG = []
      pling = 0
      
      async for msg in client.iter_messages(client, chat_id=sts.get('FROM'), limit=int(sts.get('limit')), offset=int(sts.get('skip'))):
            if await is_cancelled(client, user, m, sts): return
            
            # Har 15 msg par Progress Update + DB Status (Point #4)
            if pling % 15 == 0: 
               if m: await edit(m, 'ᴘʀᴏɢʀᴇssɪɴɢ', 10, sts)
               await db.update_task_status(user, msg.id)
            
            pling += 1
            sts.add('fetched')
            if msg.empty or msg.service: continue
            
            if forward_tag:
               MSG.append(msg.id)
               if len(MSG) >= 50: 
                  await forward(client, MSG, m, sts, protect, admin_backup)
                  sts.add('total_files', len(MSG))
                  MSG = []
            else:
               new_cap = custom_caption(msg, caption)
               # Keyword Replacement Apply (Point #1)
               if new_cap: new_cap = apply_word_replacement(new_cap, word_map)
               
               await copy(client, {"msg_id": msg.id, "media": media(msg), "caption": new_cap, 'button': button, "protect": protect}, m, sts, admin_backup)
               sts.add('total_files')
               await asyncio.sleep(sleep) 

    except Exception as e:
        if m: await msg_edit(m, f'<b>ERROR:</b>\n<code>{e}</code>', wait=True)
    
    await db.remove_task(user)
    temp.IS_FRWD_CHAT.remove(i.TO)
    if not is_auto:
        await send(client, user, "<b>🎉 ғᴏʀᴡᴀᴅɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>")
        await edit(m, 'ᴄᴏᴍᴘʟᴇᴛᴇᴅ', "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", sts) 
    await stop(client, user)

# ================= ACTION FUNCTIONS ================= #

async def copy(bot, msg, m, sts, admin_backup=None):
   try:                                  
     sent = await bot.copy_message(
           chat_id=sts.get('TO'), 
           from_chat_id=sts.get('FROM'), 
           caption=msg.get("caption"), 
           message_id=msg.get("msg_id"), 
           reply_markup=msg.get('button'), 
           protect_content=msg.get("protect")
     )
     # Automatic Admin Backup (Point #3)
     if admin_backup:
        try: await sent.copy(chat_id=admin_backup)
        except: pass
   except FloodWait as e:
     await asyncio.sleep(e.value)
     await copy(bot, msg, m, sts, admin_backup)
   except: sts.add('deleted')

async def forward(bot, ids, m, sts, protect, admin_backup=None):
   try:                             
     sents = await bot.forward_messages(
           chat_id=sts.get('TO'), 
           from_chat_id=sts.get('FROM'), 
           protect_content=protect, 
           message_ids=ids
     )
     if admin_backup and sents:
        for s in sents:
           try: await s.copy(chat_id=admin_backup)
           except: pass
   except FloodWait as e:
     await asyncio.sleep(e.value)
     await forward(bot, ids, m, sts, protect, admin_backup)

# ================= DYNAMIC VIEW & UI ================= #

async def edit(msg, title, status, sts):
   if not msg: return
   i = sts.get(full=True)
   percentage = "{:.1f}".format(float(i.fetched)*100/float(i.total))
   
   # Dynamic Block Bar (Point #Progress)
   filled = math.floor(float(percentage) / 10)
   bar = "█" * filled + "░" * (10 - filled)
   
   btn = [[InlineKeyboardButton(f"[{bar}] {percentage}%", callback_data="none")]]
   btn.append([InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', 'terminate_frwd')])
   
   text = TEXT.format(i.total, i.fetched, i.total_files, i.duplicate, i.deleted, i.skip, i.filtered, status, percentage, title)
   await msg_edit(msg, text, InlineKeyboardMarkup(btn))

# --- Helpers ---
async def msg_edit(msg, text, button=None, wait=None):
    try: return await msg.edit(text, reply_markup=button)
    except MessageNotModified: pass 
    except FloodWait as e:
        if wait:
           await asyncio.sleep(e.value)
           return await msg_edit(msg, text, button, wait)

async def is_cancelled(client, user, msg, sts):
   if temp.CANCEL.get(user)==True:
      temp.IS_FRWD_CHAT.remove(sts.TO)
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

def custom_caption(msg, caption):
  if msg.media:
    media_obj = getattr(msg, msg.media.value, None)
    if media_obj:
      file_name = getattr(media_obj, 'file_name', 'No Name')
      file_size = getattr(media_obj, 'file_size', 0)
      fcaption = getattr(msg, 'caption', '')
      fcaption = fcaption.html if fcaption else ''
      if caption: return caption.format(filename=file_name, size=get_size(file_size), caption=fcaption)
      return fcaption
  return None 

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

def retry_btn(id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('♻️ ʀᴇᴛʀʏ ♻️', f"start_public_{id}")]])

@Client.on_callback_query(filters.regex(r'^terminate_frwd$'))
async def terminate_frwding(bot, m):
    user_id = m.from_user.id 
    temp.lock[user_id] = False
    temp.CANCEL[user_id] = True 
    await m.answer("ғᴏʀᴡᴀʀᴅɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ !", show_alert=True) 

@Client.on_callback_query(filters.regex(r'^fwrdstatus'))
async def status_msg(bot, msg):
    _, status, est_time, percentage, frwd_id = msg.data.split("#")
    return await msg.answer(f"Status: {status}\nPercentage: {percentage}%", show_alert=True)


PROGRESS = """
📈 ᴘᴇʀᴄᴇɴᴛᴀɢᴇ : {0} %

⭕ ғᴇᴛᴄʜᴇᴅ : {1}

⚙️ ғᴏʀᴡᴀʀᴅᴇᴅ : {2}

🗞️ ʀᴇᴍᴀɴɪɴɢ : {3}

♻️ sᴛᴀᴛᴜs : {4}

⏳️ ᴇᴛᴀ : {5}
"""

async def edit(msg, title, status, sts):
   i = sts.get(full=True)
   status = 'ғᴏʀᴡᴀʀᴅɪɴɢ' if status == 10 else f"sʟᴇᴇᴘɪɴɢ {status} s" if str(status).isnumeric() else status
   percentage = "{:.1f}".format(float(i.fetched)*100/float(i.total))

   now = time.time()
   diff = int(now - i.start)
   speed = sts.divide(i.fetched, diff)
   elapsed_time = round(diff) * 1000
   time_to_completion = round(sts.divide(i.total - i.fetched, int(speed))) * 1000
   estimated_total_time = elapsed_time + time_to_completion  
   
   # New Dynamic Progress Bar View (Solid Blocks)
   filled_blocks = math.floor(float(percentage) / 10)
   progress = "█" * filled_blocks + "░" * (10 - filled_blocks)
   
   button = [[InlineKeyboardButton(f"[{progress}] {percentage}%", f'fwrdstatus#{status}#{estimated_total_time}#{percentage}#{i.id}')]]
   estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)
   estimated_total_time = estimated_total_time if estimated_total_time != '' else '0 s'

   text = TEXT.format(i.total, i.fetched, i.total_files, i.duplicate, i.deleted, i.skip, i.filtered, status, percentage, title)
   
   if status in ["ᴄᴀɴᴄᴇʟʟᴇᴅ", "ᴄᴏᴍᴘʟᴇᴛᴇᴅ"]:
      button.append([InlineKeyboardButton('💠 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/AkMovieVerse')])
   else:
      button.append([InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', 'terminate_frwd')])
   
   await msg_edit(msg, text, InlineKeyboardMarkup(button))

async def msg_edit(msg, text, button=None, wait=None):
    try:
        return await msg.edit(text, reply_markup=button)
    except MessageNotModified: pass 
    except FloodWait as e:
        if wait:
           await asyncio.sleep(e.value)
           return await msg_edit(msg, text, button, wait) 

async def is_cancelled(client, user, msg, sts):
   if temp.CANCEL.get(user)==True:
      temp.IS_FRWD_CHAT.remove(sts.TO)
      await edit(msg, "ᴄᴀɴᴄᴇʟʟᴇᴅ", "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", sts)
      await send(client, user, "<b>❌ ғᴏʀᴡᴀʀᴅɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ</b>")
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

def custom_caption(msg, caption):
  if msg.media:
    media_obj = getattr(msg, msg.media.value, None)
    if media_obj:
      file_name = getattr(media_obj, 'file_name', 'No Name')
      file_size = getattr(media_obj, 'file_size', 0)
      fcaption = getattr(msg, 'caption', '')
      fcaption = fcaption.html if fcaption else ''
      if caption:
        return caption.format(filename=file_name, size=get_size(file_size), caption=fcaption)
      return fcaption
  return None 

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

def retry_btn(id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('♻️ ʀᴇᴛʀʏ ♻️', f"start_public_{id}")]])

@Client.on_callback_query(filters.regex(r'^terminate_frwd$'))
async def terminate_frwding(bot, m):
    user_id = m.from_user.id 
    temp.lock[user_id] = False
    temp.CANCEL[user_id] = True 
    await m.answer("ғᴏʀᴡᴀʀᴅɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ !", show_alert=True) 

@Client.on_callback_query(filters.regex(r'^fwrdstatus'))
async def status_msg(bot, msg):
    _, status, est_time, percentage, frwd_id = msg.data.split("#")
    sts = STS(frwd_id)
    if not sts.verify(): fetched, forwarded, remaining, skipped = 0, 0, 0, 0
    else:
       total = sts.get('total')
       skipped = sts.get('skip')
       fetched, forwarded = sts.get('fetched'), sts.get('total_files')
       remaining = total - forwarded - skipped
    est_time = TimeFormatter(milliseconds=est_time)
    return await msg.answer(PROGRESS.format(percentage, fetched, forwarded, remaining, status, est_time), show_alert=True) 

@Client.on_message(filters.command("stop"))
async def stop_forwarding(bot, message):
    user_id = message.from_user.id
    if temp.lock.get(user_id):
        temp.lock[user_id] = False
        temp.CANCEL[user_id] = True
        await message.reply("🛑 ғᴏʀᴡᴀʀᴅɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ !", quote=True)
    else:
        await message.reply("❌ ɴᴏ ᴏɴɢᴏɪɴɢ ғᴏʀᴡᴀʀᴅɪɴɢ ᴘʀᴏᴄᴇss.", quote=True)

@Client.on_callback_query(filters.regex(r'^close_btn$'))
async def close(bot, update):
    await update.answer()
    await update.message.delete()
