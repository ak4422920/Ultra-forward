import os
import re 
import sys
import asyncio 
import logging 
from database import db 
from config import Config, temp
from pyrogram import Client, filters
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

# --- Regex for Button Parsing ---
BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)]\[buttonurl:/{0,2}(.+?)(:same)?])")

# ================= CONFIGURATION MANAGER ================= #

async def get_configs(user_id):
    """Database se user ki saari settings uthata hai."""
    return await db.get_configs(user_id)

async def update_configs(user_id, key, value):
    """
    User settings update karne ka dimag.
    Saare naye features (Thumbnail, Mapper, Targets) yahan register hain.
    """
    current = await db.get_configs(user_id)
    
    # Elite V3 Features Keys
    root_keys = [
        'caption', 'duplicate', 'db_uri', 'forward_tag', 
        'protect', 'file_size', 'button', 'replace_words', 
        'admin_backup', 'thumbnail', 'targets' #
    ]
    
    if key in root_keys:
        current[key] = value
    else: 
        if 'filters' not in current: current['filters'] = {}
        current['filters'][key] = value
        
    await db.update_configs(user_id, current)

# ================= WORKER ENGINE INITIALIZER ================= #

async def start_clone_bot(FwdBot):
   """
   Client ko start karta hai aur usme custom iterator inject karta hai.
   Isse bot deleted messages ko skip karke smoothly aage badhta hai.
   """
   if not FwdBot.is_connected:
       await FwdBot.start()
   
   async def iter_messages(chat_id, limit, offset_id=0):
        """
        Engine history scan karne ke liye get_chat_history use karega.
        """
        async for message in FwdBot.get_chat_history(chat_id, limit=limit, offset_id=offset_id):
            yield message
                
   FwdBot.iter_messages = iter_messages
   return FwdBot

# ================= CLIENT MANAGEMENT (BOT/USERBOT) ================= #

class CLIENT: 
  def __init__(self):
     self.api_id = Config.API_ID
     self.api_hash = Config.API_HASH
    
  def client(self, data, user=None):
     """
     In-Memory clients banata hai taaki server storage na bhare.
     """
     if user is None and isinstance(data, dict) and data.get('is_bot') == False:
        # Userbot Client
        return Client(
            name=f"user_{data['user_id']}", 
            api_id=self.api_id, 
            api_hash=self.api_hash, 
            session_string=data.get('session'), 
            in_memory=True
        )
     elif user is True:
        # String Session add karte waqt validation
        return Client(name="val_session", api_id=self.api_id, api_hash=self.api_hash, session_string=data, in_memory=True)
     
     # Bot Token Client
     token = data if isinstance(data, str) else data.get('token')
     return Client(name="bot_worker", api_id=self.api_id, api_hash=self.api_hash, bot_token=token, in_memory=True)
  
  async def add_bot(self, bot, message):
     """Bot Token se worker add karna."""
     user_id = int(message.from_user.id)
     prompt = "<b>1) @BotFather se ek bot banayein.\n2) Uska API Token copy karein.\n3) Wo token mujhe yahan bhej dein.\n\n/cancel - To Stop.</b>"
     msg = await bot.ask(chat_id=user_id, text=prompt)
     if msg.text == '/cancel': return await msg.reply('❌ Action Cancelled!')
     
     token_match = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', msg.text)
     bot_token = token_match[0] if token_match else None
     if not bot_token: return await msg.reply_text("<b>❌ Invalid Token Format!</b>")
       
     sts = await msg.reply_text("<code>Verifying Bot Token...</code>")
     try:
       _client = await start_clone_bot(self.client(bot_token, False))
       _bot = _client.me
       details = {
           'id': _bot.id, 'is_bot': True, 'user_id': user_id, 
           'name': _bot.first_name, 'token': bot_token, 'username': _bot.username
       }
       await db.add_bot(details)
       await sts.edit(f"<b>✅ Bot Added Successfully!</b>\n\n<b>Name:</b> {_bot.first_name}\n<b>Username:</b> @{_bot.username}")
       await _client.stop()
       return True
     except Exception as e:
       await sts.edit(f"<b>❌ Error:</b> `{e}`")
       return False

  async def add_login(self, bot, message):
    """Phone number aur OTP flow (Safe & Secure)."""
    user_id = int(message.from_user.id)
    await bot.send_message(user_id, "<b>📲 Please send your Phone Number with Country Code.\nExample: <code>+919876543210</code>\n/cancel - To cancel.</b>")
    phone_msg = await bot.ask(user_id, "Aapka number?", filters=filters.text)
    if phone_msg.text.startswith('/'): return
        
    client = Client(name="user", api_id=self.api_id, api_hash=self.api_hash, in_memory=True)
    await client.connect()
    
    try:
        code = await client.send_code(phone_msg.text)
        prompt_otp = "<b>📩 OTP bhej diya gaya hai.</b>\n\nOTP ke beech mein space dein (Example: <code>1 2 3 4 5</code>)."
        otp_msg = await bot.ask(user_id, prompt_otp, filters=filters.text, timeout=600)
        await client.sign_in(phone_msg.text, code.phone_code_hash, otp_msg.text.replace(" ", ""))
    except SessionPasswordNeeded:
        pwd = await bot.ask(user_id, "<b>🔐 2FA Password:</b>\n\nAapka account Protected hai, password bhejye.", filters=filters.text)
        await client.check_password(password=pwd.text)
    except Exception as e:
        return await bot.send_message(user_id, f"<b>❌ Login Error:</b> `{e}`")

    string_session = await client.export_session_string()
    user = await client.get_me()
    await db.add_bot({
        'id': user.id, 'is_bot': False, 'user_id': user_id, 
        'name': user.first_name, 'session': string_session, 'username': user.username
    })
    await bot.send_message(user_id, f"<b>✅ Userbot Logged In!</b>\n\n<b>Name:</b> {user.first_name}")
    await client.disconnect()
    return True

# ================= BUTTON PARSER ================= #

def parse_buttons(text, markup=True):
    """[Name][buttonurl:link] format ko Telegram buttons mein badalta hai."""
    buttons = []
    if not text: return None
    for match in BTN_URL_REGEX.finditer(text):
        if bool(match.group(4)) and buttons:
            buttons[-1].append(InlineKeyboardButton(text=match.group(2), url=match.group(3).replace(" ", "")))
        else:
            buttons.append([InlineKeyboardButton(text=match.group(2), url=match.group(3).replace(" ", ""))])
    
    if markup and buttons: return InlineKeyboardMarkup(buttons)
    return buttons if buttons else None
