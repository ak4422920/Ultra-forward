import re
import asyncio 
from .utils import STS
from database import db
from config import temp, Config
from translation import Translation
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

# =================== HELPERS =================== #

def extract_id(text):
    if not text: return None
    # Regex to handle links and raw IDs
    regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
    match = regex.match(text.replace("?single", ""))
    if match:
        chat_id = match.group(4)
        if chat_id.isnumeric(): return int(("-100" + chat_id))
        return chat_id
    # Raw ID check
    if text.startswith("-100") or text.isdigit():
        return text.replace(" ", "")
    return None

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
    from_input = await bot.ask(user_id, Translation.FROM_MSG)
    if from_input.text and from_input.text.startswith('/'):
        return await message.reply(Translation.CANCEL)
    
    chat_id = None
    if from_input.forward_from_chat:
        chat_id = from_input.forward_from_chat.id
    else:
        chat_id = extract_id(from_input.text)
    
    if not chat_id:
        return await message.reply("<b>❌ Invalid Source!</b> Link ya ID sahi nahi hai.")

    # 4. 📥 Target Selection
    configs = await db.get_configs(user_id)
    saved_targets = configs.get('targets')
    
    t_btn = []
    if saved_targets:
        # Button logic: Hum callback mein source_id aur saved_targets dono pass karenge
        t_btn.append([InlineKeyboardButton("🎯 Use Saved Targets", callback_data=f"set_trg_saved_{chat_id}")])
    t_btn.append([InlineKeyboardButton("❌ Cancel Setup", callback_data="close_btn")])
    
    target_prompt = await bot.send_message(
        user_id, 
        Translation.TO_MSG + (f"\n\n<b>Saved:</b> <code>{saved_targets}</code>" if saved_targets else ""),
        reply_markup=InlineKeyboardMarkup(t_btn)
    )

    # User ke response ka wait: Ya toh wo ID type karega ya button dabayega
    # Agar button dabaya toh handle_target (niche wala) function kaam sambhaal lega
    to_input = await bot.listen(user_id)
    
    if to_input.text:
        if to_input.text.startswith('/'): return
        target_ids = to_input.text.replace(" ", "")
        await skip_step(bot, user_id, chat_id, target_ids)

# =================== CALLBACK & STEPS =================== #

@Client.on_callback_query(filters.regex(r'^set_trg_saved_'))
async def handle_saved_target(bot, query):
    user_id = query.from_user.id
    source_id = query.data.split("_")[3]
    
    configs = await db.get_configs(user_id)
    target_ids = configs.get('targets')
    
    await query.message.delete()
    await skip_step(bot, user_id, source_id, target_ids)

async def skip_step(bot, user_id, source_id, target_ids):
    # 5. ⏩ Skip Messages
    skip_msg = await bot.ask(user_id, Translation.SKIP_MSG)
    if skip_msg.text and skip_msg.text.startswith('/'): return
    
    skip_val = int(skip_msg.text) if skip_msg.text.isdigit() else 0

    # 6. 📋 Confirmation UI
    # STS store karne ke liye hum user_id ko hi forward_id banayenge (Simple & Clean)
    forward_id = str(user_id)
    
    confirm_text = (
        "<b>📋 ꜰᴏʀᴡᴀʀᴅɪɴɢ sᴇᴛᴜᴘ ʀᴇᴀᴅʏ</b>\n\n"
        f"<b>📤 Source:</b> <code>{source_id}</code>\n"
        f"<b>📥 Targets:</b> <code>{target_ids}</code>\n"
        f"<b>⏩ Skip:</b> <code>{skip_val}</code>\n\n"
        "<i>Ready to launch?</i>"
    )

    buttons = [[
        InlineKeyboardButton('🚀 Start Now', callback_data=f"start_public_{forward_id}"),
        InlineKeyboardButton('❌ Cancel', callback_data="close_btn")
    ]]

    # Store in memory BEFORE showing start button
    STS(forward_id).store(source_id, target_ids, skip_val, 0)
    
    await bot.send_message(user_id, text=confirm_text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r'^close_btn'))
async def close_callback(bot, query):
    await query.message.delete()
