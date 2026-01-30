import re
import asyncio 
from .utils import STS
from database import db
from config import temp, Config
from translation import Translation
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

# =================== FORWARD SETUP COMMAND =================== #

@Client.on_message(filters.private & filters.command(["forward", "fwd"]))
async def run(bot, message):
    user_id = message.from_user.id
    
    # 1. 🤖 Worker Check
    _bot = await db.get_bot(user_id)
    if not _bot:
      return await message.reply("<b>❌ Error:</b>\nAapne koi Worker add nahi kiya hai. Pehle /settings mein jayein.")
    
    # 2. 🔒 Lock Check
    if temp.lock.get(user_id):
        return await message.reply("<b>❌ Error:</b> Ek task pehle se chal raha hai.")

    # 3. 📤 Source Selection
    from_input = await bot.ask(message.chat.id, Translation.FROM_MSG)
    if from_input.text and from_input.text.startswith('/'):
        return await message.reply(Translation.CANCEL)
    
    chat_id = None
    if from_input.text:
        # Improved Regex for all types of links
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(from_input.text.replace("?single", ""))
        if match:
            chat_id = match.group(4)
            if chat_id.isnumeric(): chat_id = int(("-100" + chat_id))
        else:
            return await message.reply('<b>❌ Invalid Link!</b> Sahi message link bhejein.')
    elif from_input.forward_from_chat:
        chat_id = from_input.forward_from_chat.id
    
    if not chat_id:
        return await message.reply("<b>❌ Error:</b> Source channel ki pehchan nahi ho saki.")

    # 4. 📥 Target Selection (Saved Targets Integration)
    configs = await db.get_configs(user_id)
    saved_targets = configs.get('targets')
    
    t_btn = None
    t_text = Translation.TO_MSG
    
    if saved_targets:
        t_text += f"\n\n<b>🎯 Saved Targets:</b>\n<code>{saved_targets}</code>\n\nNiche button dabiye ya naya ID bhejein."
        t_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Use Saved Targets", callback_data="use_saved_targets")]])
    
    to_input = await bot.ask(message.chat.id, t_text, reply_markup=t_btn)
    
    if to_input.text and to_input.text.startswith('/'):
        return await message.reply(Translation.CANCEL)

    # Logic: Agar button dabaya toh to_input.text khali hoga
    target_ids = saved_targets if not to_input.text else to_input.text.replace(" ", "")

    # 5. ⏩ Skip Messages
    skip_input = await bot.ask(message.chat.id, Translation.SKIP_MSG)
    if skip_input.text and skip_input.text.startswith('/'):
        return await message.reply(Translation.CANCEL)
    
    skip_val = int(skip_input.text) if skip_input.text.isdigit() else 0

    # 6. 📋 Confirmation UI
    forward_id = f"{user_id}_{int(asyncio.get_event_loop().time())}"
    
    confirm_text = (
        "<b>📋 ꜰᴏʀᴡᴀʀᴅɪɴɢ sᴇᴛᴜᴘ ʀᴇᴀᴅʏ</b>\n\n"
        f"<b>📤 Source:</b> <code>{chat_id}</code>\n"
        f"<b>📥 Targets:</b> <code>{target_ids}</code>\n"
        f"<b>⏩ Skip:</b> <code>{skip_val}</code>\n\n"
        "<i>Ready to launch?</i>"
    )

    buttons = [[
        InlineKeyboardButton('🚀 Start Now', callback_data=f"start_public_{forward_id}"),
        InlineKeyboardButton('❌ Cancel', callback_data="close_btn")
    ]]

    await message.reply_text(text=confirm_text, reply_markup=InlineKeyboardMarkup(buttons))
    
    # Store in memory
    STS(forward_id).store(chat_id, target_ids, skip_val, 0)

# =================== CALLBACK HANDLERS =================== #

@Client.on_callback_query(filters.regex(r'^close_btn'))
async def close_callback(bot, query):
    await query.message.delete()

@Client.on_callback_query(filters.regex(r'^use_saved_targets'))
async def use_saved_callback(bot, query):
    # Answer query and edit message to remove buttons so 'ask' continues
    await query.answer("✅ Saved Targets Selected!", show_alert=False)
    await query.message.edit_text("<b>🎯 Saved Targets Selected!</b>\nAb agla step follow karein...")
