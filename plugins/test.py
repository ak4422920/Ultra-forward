import os
import re 
import sys
import typing
import asyncio 
import logging 
from database import db 
from config import Config, temp
from pyrogram import Client, filters, types
from pyrogram.raw.all import layer
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 
from pyrogram.errors import (
    AccessTokenExpired, 
    AccessTokenInvalid, 
    FloodWait, 
    PhoneNumberInvalid, 
    PhoneCodeInvalid, 
    PhoneCodeExpired, 
    SessionPasswordNeeded, 
    PasswordHashInvalid
)
from translation import Translation
from typing import Union, Optional, AsyncGenerator

logger = logging.getLogger(__name__)

BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)]\[buttonurl:/{0,2}(.+?)(:same)?])")
BOT_TOKEN_TEXT = "<b>1) Create a bot using @BotFather\n2) Then you will get a message with bot token\n3) Forward that message to me</b>"

# ================= CONFIG HELPERS (Crucial for Settings.py) ================= #

async def get_configs(user_id):
    """Point #1: Fetching user configurations from database."""
    return await db.get_configs(user_id)

async def update_configs(user_id, key, value):
    """Point #2: Centralized function to update specific user configurations."""
    current = await db.get_configs(user_id)
    
    # List of keys that live in the root of the config dict
    root_keys = [
        'caption', 'duplicate', 'db_uri', 'forward_tag', 
        'protect', 'file_size', 'size_limit', 'extension', 
        'keywords', 'button', 'replace_words', 'admin_backup', 'thumbnail'
    ]
    
    if key in root_keys:
        current[key] = value
    else: 
        # If not in root, it's a filter setting inside the 'filters' sub-dict
        if 'filters' not in current:
            current['filters'] = {}
        current['filters'][key] = value
        
    await db.update_configs(user_id, current)

# ================= WORKER INITIALIZATION ================= #

async def start_clone_bot(FwdBot, data=None):
   """Monkey-patches the client to add a custom message iterator."""
   await FwdBot.start()
   
   async def iter_messages(
      self, 
      chat_id: Union[int, str], 
      limit: int, 
      offset: int = 0
      ) -> Optional[AsyncGenerator["types.Message", None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            ids = [i for i in range(current, current + new_diff + 1)]
            try:
                messages = await self.get_messages(chat_id, ids)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                messages = await self.get_messages(chat_id, ids)
                
            for message in messages:
                yield message
                current += 1
                
   FwdBot.iter_messages = iter_messages
   return FwdBot

# ================= CLIENT MANAGEMENT CLASS ================= #

class CLIENT: 
  def __init__(self):
     self.api_id = Config.API_ID
     self.api_hash = Config.API_HASH
    
  def client(self, data, user=None):
     """Initializes either a Bot or a Userbot client."""
     if user == None and data.get('is_bot') == False:
        return Client("USERBOT", self.api_id, self.api_hash, session_string=data.get('session'))
     elif user == True:
        return Client("USERBOT", self.api_id, self.api_hash, session_string=data)
     elif user != False:
        data = data.get('token')
     return Client("BOT", self.api_id, self.api_hash, bot_token=data, in_memory=True)
  
  async def add_bot(self, bot, message):
     """Logic to add a worker bot via token."""
     user_id = int(message.from_user.id)
     msg = await bot.ask(chat_id=user_id, text=BOT_TOKEN_TEXT)
     if msg.text == '/cancel':
        return await msg.reply('<b>Process cancelled!</b>')
     
     bot_token = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', msg.text, re.IGNORECASE)
     bot_token = bot_token[0] if bot_token else None
     
     if not bot_token:
       return await msg.reply_text("<b>Invalid Token: No bot token found.</b>")
       
     try:
       _client = await start_clone_bot(self.client(bot_token, False), True)
       _bot = _client.me
       details = {
         'id': _bot.id,
         'is_bot': True,
         'user_id': user_id,
         'name': _bot.first_name,
         'token': bot_token,
         'username': _bot.username 
       }
       await db.add_bot(details)
       await _client.stop()
       return True
     except Exception as e:
       await msg.reply_text(f"<b>BOT ERROR:</b> `{e}`")
       return False

  async def add_login(self, bot, message):
    """Direct login logic for Userbots."""
    user_id = int(message.from_user.id)
    api_id = Config.API_ID
    api_hash = Config.API_HASH
    
    await bot.send_message(user_id, "<b>➫ Please send your Phone Number with Country Code.\nExample: +910000000000\n/cancel - To cancel.</b>")
    phone_number_msg = await bot.ask(user_id, "Waiting for phone number...", filters=filters.text)
    
    if phone_number_msg.text.startswith('/'):
        return await bot.send_message(user_id, "<b>Process cancelled!</b>")
        
    phone_number = phone_number_msg.text
    client = Client(name="user", api_id=api_id, api_hash=api_hash, in_memory=True)
    await client.connect()
    
    try:
        code = await client.send_code(phone_number)
    except PhoneNumberInvalid:
        await bot.send_message(user_id, "<b>Invalid Phone Number. Restart process.</b>")
        return

    try:
        phone_code_msg = await bot.ask(user_id, "Please send the OTP.\n➫ If OTP is 12345, send as 1 2 3 4 5.", filters=filters.text, timeout=600)
        if phone_code_msg.text.startswith('/'): return
    except asyncio.TimeoutError:
        return await bot.send_message(user_id, "Time limit reached.")

    phone_code = phone_code_msg.text.replace(" ", "")
    try:
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except SessionPasswordNeeded:
        two_step_msg = await bot.ask(user_id, "Enter your Two-Step Password.", filters=filters.text, timeout=300)
        try:
            await client.check_password(password=two_step_msg.text)
        except Exception as e:
            return await bot.send_message(user_id, f"Password Error: {e}")
    except Exception as e:
        return await bot.send_message(user_id, f"Login Error: {e}")

    string_session = await client.export_session_string()
    user = await client.get_me()
    details = {
        'id': user.id,
        'is_bot': False,
        'user_id': user_id,
        'name': user.first_name,
        'session': string_session,
        'username': user.username
    }
    await db.add_bot(details)
    await client.disconnect()
    return details    

  async def add_session(self, bot, message):
     """Adding an existing Pyrogram String Session."""
     user_id = int(message.from_user.id)
     msg = await bot.ask(chat_id=user_id, text="<b>Send your Pyrogram Session String.\n\n/cancel - To cancel.</b>")
     if msg.text == '/cancel': return
     
     try:
       client = await start_clone_bot(self.client(msg.text, True), True)
       user = client.me
       details = {
         'id': user.id,
         'is_bot': False,
         'user_id': user_id,
         'name': user.first_name,
         'session': msg.text,
         'username': user.username
       }
       await db.add_bot(details)
       await client.stop()
       return True
     except Exception as e:
       await msg.reply_text(f"<b>USER BOT ERROR:</b> `{e}`")

# ================= BUTTON PARSER ================= #

def parse_buttons(text, markup=True):
    """Parses custom button strings like [Name][buttonurl:link]."""
    buttons = []
    if not text:
        return None
    for match in BTN_URL_REGEX.finditer(text):
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        if n_escapes % 2 == 0:
            if bool(match.group(4)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(3).replace(" ", "")))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(3).replace(" ", ""))])
    
    if markup and buttons:
       return InlineKeyboardMarkup(buttons)
    return buttons if buttons else None
