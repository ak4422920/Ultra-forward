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

# Aapka purana regex aur text
BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)]\[buttonurl:/{0,2}(.+?)(:same)?])")
BOT_TOKEN_TEXT = "<b>1) Create a bot using @BotFather\n2) Then you will get a message with bot token\n3) Forward that message to me</b>"

# ================= CONFIG HELPERS ================= #

async def get_configs(user_id):
    """Database se user settings fetch karta hai."""
    return await db.get_configs(user_id)

async def update_configs(user_id, key, value):
    """User settings ko update karne ka centralized function."""
    current = await db.get_configs(user_id)
    root_keys = ['caption', 'duplicate', 'db_uri', 'forward_tag', 'protect', 'file_size', 'button', 'replace_words', 'admin_backup', 'thumbnail']
    
    if key in root_keys:
        current[key] = value
    else: 
        if 'filters' not in current: current['filters'] = {}
        current['filters'][key] = value
    await db.update_configs(user_id, current)

# ================= UPGRADED WORKER ENGINE ================= #

async def start_clone_bot(FwdBot, data=None):
   """
   Logic Upgrade: Deleted messages handle karne ke liye get_chat_history 
   ka use kiya hai.
   """
   if not FwdBot.is_connected:
       await FwdBot.start()
   
   async def iter_messages(chat_id, limit, offset=0):
        count = 0
        # Offset messages ko skip karke history uthana
        async for message in FwdBot.get_chat_history(chat_id, limit=limit, offset=offset):
            if count >= limit: break
            yield message
            count += 1
                
   FwdBot.iter_messages = iter_messages
   return FwdBot

# ================= FULL CLIENT MANAGEMENT CLASS ================= #

class CLIENT: 
  def __init__(self):
     self.api_id = Config.API_ID
     self.api_hash = Config.API_HASH
    
  def client(self, data, user=None):
     """Bot Token ya Session String se client create karna."""
     if user is None and isinstance(data, dict) and data.get('is_bot') == False:
        return Client(name=f"user_{data['user_id']}", api_id=self.api_id, api_hash=self.api_hash, session_string=data.get('session'), in_memory=True)
     elif user is True:
        return Client(name="user_session", api_id=self.api_id, api_hash=self.api_hash, session_string=data, in_memory=True)
     
     token = data if isinstance(data, str) else data.get('token')
     return Client(name="bot_worker", api_id=self.api_id, api_hash=self.api_hash, bot_token=token, in_memory=True)
  
  async def add_bot(self, bot, message):
     """Bot Token ke zariye worker add karna."""
     user_id = int(message.from_user.id)
     msg = await bot.ask(chat_id=user_id, text=BOT_TOKEN_TEXT)
     if msg.text == '/cancel': return await msg.reply('Cancelled!')
     
     token_match = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', msg.text)
     bot_token = token_match[0] if token_match else None
     if not bot_token: return await msg.reply_text("Invalid Token!")
       
     try:
       _client = await start_clone_bot(self.client(bot_token, False))
       _bot = _client.me
       details = {'id': _bot.id, 'is_bot': True, 'user_id': user_id, 'name': _bot.first_name, 'token': bot_token, 'username': _bot.username}
       await db.add_bot(details)
       await _client.stop()
       return True
     except Exception as e:
       await msg.reply_text(f"Error: {e}")
       return False

  async def add_login(self, bot, message):
    """Phone number aur OTP se login."""
    user_id = int(message.from_user.id)
    await bot.send_message(user_id, "<b>➫ Please send your Phone Number with Country Code.\nExample: +910000000000\n/cancel - To cancel.</b>")
    phone_msg = await bot.ask(user_id, "Waiting for phone number...", filters=filters.text)
    if phone_msg.text.startswith('/'): return
        
    client = Client(name="user", api_id=self.api_id, api_hash=self.api_hash, in_memory=True)
    await client.connect()
    
    try:
        code = await client.send_code(phone_msg.text)
        otp_msg = await bot.ask(user_id, "Please send the OTP.\n➫ Example: 1 2 3 4 5", filters=filters.text, timeout=600)
        await client.sign_in(phone_msg.text, code.phone_code_hash, otp_msg.text.replace(" ", ""))
    except SessionPasswordNeeded:
        pwd = await bot.ask(user_id, "Enter 2FA Password", filters=filters.text)
        await client.check_password(password=pwd.text)
    except Exception as e:
        return await bot.send_message(user_id, f"Login Error: {e}")

    string_session = await client.export_session_string()
    user = await client.get_me()
    await db.add_bot({'id': user.id, 'is_bot': False, 'user_id': user_id, 'name': user.first_name, 'session': string_session, 'username': user.username})
    await client.disconnect()
    return True

  async def add_session(self, bot, message):
     """Direct Session String add karna."""
     user_id = int(message.from_user.id)
     msg = await bot.ask(chat_id=user_id, text="<b>Send your Pyrogram Session String.\n\n/cancel - To cancel.</b>")
     if msg.text == '/cancel': return
     
     try:
       _client = await start_clone_bot(self.client(msg.text, True))
       user = _client.me
       await db.add_bot({'id': user.id, 'is_bot': False, 'user_id': user_id, 'name': user.first_name, 'session': msg.text, 'username': user.username})
       await _client.stop()
       return True
     except Exception as e:
       await msg.reply_text(f"Session Error: {e}")

# ================= BUTTON PARSER ================= #

def parse_buttons(text, markup=True):
    """Aapka purana button parser logic."""
    buttons = []
    if not text: return None
    for match in BTN_URL_REGEX.finditer(text):
        if bool(match.group(4)) and buttons:
            buttons[-1].append(InlineKeyboardButton(text=match.group(2), url=match.group(3).replace(" ", "")))
        else:
            buttons.append([InlineKeyboardButton(text=match.group(2), url=match.group(3).replace(" ", ""))])
    
    if markup and buttons: return InlineKeyboardMarkup(buttons)
    return buttons if buttons else None
