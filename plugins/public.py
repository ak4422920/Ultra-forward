import re
import asyncio 
from .utils import STS
from database import db
from config import temp 
from translation import Translation
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait 
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate as PrivateChat
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified, ChannelPrivate
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
 
# =================== FORWARD SETUP FUNCTION =================== #

@Client.on_message(filters.private & filters.command(["fwd", "forward"]))
async def run(bot, message):
    buttons = []
    btn_data = {}
    user_id = message.from_user.id
    
    # Check if worker bot is added
    _bot = await db.get_bot(user_id)
    if not _bot:
      return await message.reply("<b>❌ Error:</b>\nYou haven't added any Bot/Userbot. Please add one in /settings first.")
    
    # Check if target channels are set
    channels = await db.get_user_channels(user_id)
    if not channels:
       return await message.reply_text("<b>❌ Error:</b>\nPlease set a Target Channel in /settings before forwarding.")

    # Target Selection Logic
    if len(channels) > 1:
       for channel in channels:
          buttons.append([KeyboardButton(f"{channel['title']}")])
          btn_data[channel['title']] = channel['chat_id']
       buttons.append([KeyboardButton("Cancel")]) 
       
       _toid = await bot.ask(message.chat.id, Translation.TO_MSG, reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
       
       if _toid.text.lower() in ['/cancel', 'cancel']:
          return await message.reply_text(Translation.CANCEL, reply_markup=ReplyKeyboardRemove())
       
       to_title = _toid.text
       toid = btn_data.get(to_title)
       if not toid:
          return await message.reply_text("<b>❌ Wrong channel chosen!</b>", reply_markup=ReplyKeyboardRemove())
    else:
       toid = channels[0]['chat_id']
       to_title = channels[0]['title']

    # Source Selection Logic
    fromid = await bot.ask(message.chat.id, Translation.FROM_MSG, reply_markup=ReplyKeyboardRemove())
    
    if fromid.text and fromid.text.startswith('/'):
        return await message.reply(Translation.CANCEL)
    
    # Extract Chat ID and Last Message ID
    if fromid.text and not fromid.forward_date:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(fromid.text.replace("?single", ""))
        if not match:
            return await message.reply('<b>❌ Invalid link provided!</b>')
        
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id = int(("-100" + chat_id))
    elif fromid.forward_from_chat:
        if fromid.forward_from_chat.type != enums.ChatType.CHANNEL:
            return await message.reply_text("<b>❌ Error:</b> Source must be a Channel.")
            
        last_msg_id = fromid.forward_from_message_id
        chat_id = fromid.forward_from_chat.username or fromid.forward_from_chat.id
        
        if last_msg_id is None:
           return await message.reply_text("<b>❌ Anonymous Admin Alert:</b> Please send the last message LINK instead of forwarding.")
    else:
        return await message.reply_text("<b>❌ Invalid Input!</b>")

    # Fetching Source Title for Confirmation
    try:
        source_info = await bot.get_chat(chat_id)
        title = source_info.title
    except (PrivateChat, ChannelPrivate, ChannelInvalid):
        title = "Private Chat/Restricted"
    except Exception:
        title = "Source Chat"

    # Skip Number Logic
    skipno = await bot.ask(message.chat.id, Translation.SKIP_MSG)
    if skipno.text.startswith('/'):
        return await message.reply(Translation.CANCEL)
    
    try:
        skip_val = int(skipno.text)
    except:
        skip_val = 0

    # Task Storage for Engine
    forward_id = f"{user_id}-{skipno.id}"
    buttons = [[
        InlineKeyboardButton('✅ Yes, Start', callback_data=f"start_public_{forward_id}"),
        InlineKeyboardButton('❌ No, Cancel', callback_data="close_btn")
    ]]
    
    await message.reply_text(
        text=Translation.DOUBLE_CHECK.format(
            botname=_bot['name'], 
            botuname=_bot['username'], 
            from_chat=title, 
            to_chat=to_title, 
            skip=skip_val
        ),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    # Store Task Details in Memory (Regix.py will pick it from here)
    STS(forward_id).store(chat_id, toid, skip_val, last_msg_id)
