import os
import re 
import sys
import asyncio 
import logging 
from database import db 
from config import Config, temp
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message 
from pyrogram.errors import (
    FloodWait, 
    PhoneNumberInvalid, 
    SessionPasswordNeeded,
    PhoneCodeInvalid,
    PhoneCodeExpired
)
from translation import Translation

logger = logging.getLogger(__name__)

# --- Regex for Professional Button Parsing ---
# Format: [Google][buttonurl:https://google.com]
BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)]\[buttonurl:/{0,2}(.+?)(:same)?])")

# ================= CONFIGURATION MANAGER ================= #

async def get_configs(user_id):
    """Database se user ki saari settings fetch karta hai."""
    return await db.get_configs(user_id)

async def update_configs(user_id, key, value):
    """
    Elite V3 Features (Thumbnail, Mapper, Targets) ko register karne ka main function.
    """
    current = await db.get_configs(user_id)
    
    # Root level settings for fast access
    root_keys = [
        'caption', 'duplicate', 'db_uri', 'forward_tag', 
        'protect', 'file_size', 'button', 'replace_words', 
        'admin_backup', 'thumbnail', 'targets' 
    ]
    
    if key in root_keys:
        current[key] = value
    else: 
        if 'filters' not in current: 
            current['filters'] = {}
        current['filters'][key] = value
        
    await db.update_configs(user_id, current)

# ================= WORKER ENGINE INITIALIZER ================= #

async def start_clone_bot(FwdBot):
   """
   Client ko start karke usme iterator inject karta hai smoothly history scan ke liye.
   """
   if not FwdBot.is_connected:
       await FwdBot.start()
   
   async def iter_messages(chat_id, limit, offset_id=0):
        async for message in FwdBot.get_chat_history(chat_id, limit=limit, offset_id=offset_id):
            yield message
                
   FwdBot.iter_messages = iter_messages
   return FwdBot

# ================= CLIENT MANAGEMENT (ELITE V3) ================= #

class CLIENT: 
  def __init__(self):
     self.api_id = Config.API_ID
     self.api_hash = Config.API_HASH
    
  def client(self, data, user=None):
     """
     Ye function In-Memory clients banata hai.
     Fayda: Session files storage nahi bharti.
     """
     if user is None and isinstance(data, dict) and data.get('is_bot') == False:
        # Userbot (Session String)
        return Client(
            name=f"user_{data['user_id']}", 
            api_id=self.api_id, 
            api_hash=self.api_hash, 
            session_string=data.get('session'), 
            in_memory=True 
        )
     elif user is True:
        # String Session validation during login
        return Client(name="val_session", api_id=self.api_id, api_hash=self.api_hash, session_string=data, in_memory=True)
     
     # Normal Bot Worker (Token)
     token = data if isinstance(data, str) else data.get('token')
     return Client(name="bot_worker", api_id=self.api_id, api_hash=self.api_hash, bot_token=token, in_memory=True)
  
  async def add_bot(self, bot, message):
     """Bot Token ke zariye worker add karna."""
     user_id = int(message.from_user.id)
     prompt = "<b>1) @BotFather se naya bot banayein.\n2) Uska API Token copy karein.\n3) Token yahan bhej dein.\n\n/cancel - To Stop.</b>"
     msg = await bot.ask(chat_id=user_id, text=prompt)
     if msg.text == '/cancel': return await msg.reply('❌ Process Cancelled!')
     
     token_match = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', msg.text)
     bot_token = token_match[0] if token_match else None
     if not bot_token: return await msg.reply_text("<b>❌ Error:</b> Sahi token format bhejein.")
       
     sts = await msg.reply_text("<code>Authenticating Bot...</code>")
     try:
       _client = await start_clone_bot(self.client(bot_token, False))
       _bot = _client.me
       details = {
           'id': _bot.id, 'is_bot': True, 'user_id': user_id, 
           'name': _bot.first_name, 'token': bot_token, 'username': _bot.username
       }
       await db.add_bot(details)
       await sts.edit(f"<b>✅ Bot Worker Added!</b>\n\n<b>Name:</b> {_bot.first_name}")
       await _client.stop()
       return True
     except Exception as e:
       await sts.edit(f"<b>❌ Failure:</b> `{e}`")
       return False

  async def add_login(self, bot, message):
    """Phone login system (OTP + 2FA support)."""
    user_id = int(message.from_user.id)
    await bot.send_message(user_id, "<b>📲 Number bhejein (+ Country Code).\nExample: <code>+919876543210</code>\n/cancel - Stop.</b>")
    phone_msg = await bot.ask(user_id, "Mobile Number?", filters=filters.text)
    if phone_msg.text.startswith('/'): return
        
    client = Client(name="user", api_id=self.api_id, api_hash=self.api_hash, in_memory=True)
    await client.connect()
    
    try:
        code = await client.send_code(phone_msg.text)
        otp_prompt = "<b>📩 OTP check karein (Official Telegram app mein).</b>\n\nOTP ke beech mein space dein (Ex: <code>1 2 3 4 5</code>)."
        otp_msg = await bot.ask(user_id, otp_prompt, filters=filters.text, timeout=300)
        await client.sign_in(phone_msg.text, code.phone_code_hash, otp_msg.text.replace(" ", ""))
    except SessionPasswordNeeded:
        pwd = await bot.ask(user_id, "<b>🔐 2FA Security:</b>\n\nAapka password mang raha hai, bhejye.", filters=filters.text)
        await client.check_password(password=pwd.text)
    except Exception as e:
        return await bot.send_message(user_id, f"<b>❌ Login Failed:</b> `{e}`")

    string_session = await client.export_session_string()
    user = await client.get_me()
    await db.add_bot({
        'id': user.id, 'is_bot': False, 'user_id': user_id, 
        'name': user.first_name, 'session': string_session, 'username': user.username
    })
    await bot.send_message(user_id, f"<b>✅ Userbot Elite Connected!</b>\n\n<b>Name:</b> {user.first_name}")
    await client.disconnect()
    return True

# ================= BUTTON PARSER ================= #

def parse_buttons(text, markup=True):
    """[Name][buttonurl:link] ko standard Telegram buttons mein convert karta hai."""
    buttons = []
    if not text: return None
    for match in BTN_URL_REGEX.finditer(text):
        if bool(match.group(4)) and buttons:
            buttons[-1].append(InlineKeyboardButton(text=match.group(2), url=match.group(3).replace(" ", "")))
        else:
            buttons.append([InlineKeyboardButton(text=match.group(2), url=match.group(3).replace(" ", ""))])
    
    if markup and buttons: return InlineKeyboardMarkup(buttons)
    return buttons if buttons else None
