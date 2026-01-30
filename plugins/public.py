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
      return await message.reply("<b>❌ Error:</b>\nAapne koi Bot/Userbot add nahi kiya hai. Pehle /settings mein jayein.")
    
    # 2. 🔒 Lock Check
    if temp.lock.get(user_id):
        return await message.reply("<b>❌ Error:</b> Ek task pehle se chal raha hai.")

    # 3. 📤 Source Selection
    from_input = await bot.ask(message.chat.id, Translation.FROM_MSG)
    if from_input.text and from_input.text.startswith('/'):
        return await message.reply(Translation.CANCEL)
    
    chat_id = None
    if from_input.text:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(from_input.text.replace("?single", ""))
        if match:
            chat_id = match.group(4)
            if chat_id.isnumeric(): chat_id = int(("-100" + chat_id))
        else:
            return await message.reply('<b>❌ Invalid Link!</b> Sahi message link bhejein.')
    elif from_input.forward_from_chat:
        chat_id = from_input.forward_from_chat.id
    else:
        return await message.reply("<b>❌ Invalid Input!</b> Forward karein ya link bhejein.")

    # 4. 📥 Target Selection (1 to 5 Targets)
    to_input = await bot.ask(message.chat.id, Translation.TO_MSG)
    if to_input.text and to_input.text.startswith('/'):
        return await message.reply(Translation.CANCEL)
    
    # Comma separated IDs (Example: -1001, -1002)
    target_ids = to_input.text.replace(" ", "")

    # 5. ⏩ Skip Messages
    skip_input = await bot.ask(message.chat.id, Translation.SKIP_MSG)
    if skip_input.text and skip_input.text.startswith('/'):
        return await message.reply(Translation.CANCEL)
    
    skip_val = int(skip_input.text) if skip_input.text.isdigit() else 0

    # 6. 📋 Confirmation UI
    forward_id = f"{user_id}_{int(asyncio.get_event_loop().time())}"
    
    try:
        source_chat = await bot.get_chat(chat_id)
        source_title = source_chat.title
    except:
        source_title = "Source Channel"

    confirm_text = (
        "<b>📋 ꜰᴏʀᴡᴀʀᴅɪɴɢ sᴇᴛᴜᴘ ʀᴇᴀᴅʏ</b>\n\n"
        f"<b>📤 Source:</b> <code>{source_title}</code>\n"
        f"<b>📥 Targets:</b> <code>{target_ids}</code>\n"
        f"<b>⏩ Skip:</b> <code>{skip_val}</code>\n\n"
        "<i>Bot poora channel scan karega. Kya aap shuru karna chahte hain?</i>"
    )

    buttons = [[
        InlineKeyboardButton('✅ Start Now', callback_data=f"start_public_{forward_id}"),
        InlineKeyboardButton('❌ Cancel', callback_data="close_btn")
    ]]

    await message.reply_text(text=confirm_text, reply_markup=InlineKeyboardMarkup(buttons))
    
    # Memory mein store karna
    STS(forward_id).store(chat_id, target_ids, skip_val, 0)

# =================== CALLBACK HANDLERS (The Missing 1%) =================== #

@Client.on_callback_query(filters.regex(r'^close_btn'))
async def close_callback(bot, query):
    """Confirmation message ko delete karne ke liye."""
    await query.message.delete()

@Client.on_callback_query(filters.regex(r'^terminate_frwd'))
async def stop_callback(bot, query):
    """Chalte huye task ko beech mein rokne ke liye."""
    user_id = query.from_user.id
    temp.CANCEL[user_id] = True
    temp.lock[user_id] = False # Lock khol dena
    await query.answer("🛑 Task Stopping... Agli file forward nahi hogi.", show_alert=True)
    await query.message.edit_text("<b>❌ Task Cancelled by User.</b>")
