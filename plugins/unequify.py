import re
import asyncio
import logging
from database import db
from config import temp, Config
from .test import CLIENT, start_clone_bot
from translation import Translation
from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# --- Initialization ---
CLIENT_OBJ = CLIENT()
logger = logging.getLogger(__name__)

# UI Buttons (Branding & Crash-Proof)
def get_btns(is_completed=False):
    if is_completed:
        # Crash guard for singular/plural config issue
        fsub_link = getattr(Config, 'FORCE_SUB_CHANNEL', 'https://t.me/Silicon_Official')
        return InlineKeyboardMarkup([[InlineKeyboardButton('💠 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url=fsub_link)]])
    return InlineKeyboardMarkup([[InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', callback_data='terminate_frwd')]])

@Client.on_message(filters.command("unequify") & filters.private)
async def unequify_handler(bot, message):
    user_id = message.from_user.id
    temp.CANCEL[user_id] = False
    
    # 1. 🔒 Lock Check
    if temp.lock.get(user_id):
        return await message.reply("<b>❌ Error:</b> Pehle se ek task chal raha hai. Use khatam hone dein.")
    
    # 2. 🤖 Userbot Requirement (Crucial for History Scanning)
    _bot = await db.get_bot(user_id)
    if not _bot or _bot.get('is_bot'):
        return await message.reply("<b>⚠️ Userbot Zaroori Hai!</b>\n\nChannel history scan karne ke liye aapko /settings mein ja kar ek Userbot (Session) add karna hoga. Normal Bot history scan nahi kar sakta.")
    
    # 3. 📑 Input Parsing
    target = await bot.ask(user_id, text="<b>❪ ᴜɴᴇǫᴜɪғʏ sᴇᴛᴜᴘ ❫</b>\n\nJis channel se duplicates saaf karne hain, uska link bhejein ya wahan se ek message forward karein.\n\n/cancel - Task rokne ke liye.")
    if target.text and target.text.startswith("/"): return await message.reply("❌ **Process Cancelled!**")
    
    chat_id = None
    if target.text:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(target.text.replace("?single", ""))
        if match:
            chat_id = match.group(4)
            if chat_id.isnumeric(): chat_id = int(("-100" + chat_id))
        else:
            try:
                # Username handle karne ke liye
                chat = await bot.get_chat(target.text.split('/')[-1])
                chat_id = chat.id
            except: return await message.reply("<b>❌ Invalid Link!</b>")
    elif target.forward_from_chat:
        chat_id = target.forward_from_chat.id
    
    if not chat_id: return await message.reply("<b>❌ Invalid Input!</b> Sahi channel link ya message bhejein.")

    # 4. ✅ Confirmation Prompt
    confirm = await bot.ask(user_id, text=f"<b>Target Chat:</b> <code>{chat_id}</code>\n\nKya aap pakka is channel se saare duplicates delete karna chahte hain?\n\n<b>Note:</b> Ye process media files ke unique ID check karega.\n\n<b>Reply:</b> /yes ya /no")
    if not confirm.text or confirm.text.lower() != '/yes': return await confirm.reply("❌ **Cleaning Aborted.**")
    
    sts_msg = await confirm.reply("<b>⚙️ Initializing Userbot...</b>\n<i>Scanning power activate ho rahi hai.</i>")
    
    # 5. 🚀 The Cleaning Engine
    u_bot = None
    try:
        u_bot = await start_clone_bot(CLIENT_OBJ.client(_bot))
        temp.lock[user_id] = True
        
        MESSAGES_SET = set() # Unique Digital Fingerprints
        DUPLICATE_IDS = []
        total, deleted = 0, 0

        # Logic: Scanned message -> Extract File ID -> Compare with Set -> Delete if duplicate
        

        async for msg in u_bot.get_chat_history(chat_id):
            if temp.CANCEL.get(user_id): break
            
            total += 1
            if msg.media:
                # File unique ID check (Most accurate way)
                f_id = getattr(getattr(msg, msg.media.value, None), 'file_unique_id', None)
                if f_id:
                    if f_id in MESSAGES_SET:
                        DUPLICATE_IDS.append(msg.id)
                    else:
                        MESSAGES_SET.add(f_id)
            
            # Batch Progress Update
            if total % 100 == 0:
                try:
                    await sts_msg.edit(
                        f"<b>🔍 Scanning History...</b>\n\n"
                        f"• Scanned: <code>{total}</code>\n"
                        f"• Duplicates Found: <code>{len(DUPLICATE_IDS) + deleted}</code>\n\n"
                        f"<i>Bot is scanning backwards to find clones.</i>", 
                        reply_markup=get_btns()
                    )
                except: pass
            
            # Batch Deletion (Flood protection batches of 50)
            if len(DUPLICATE_IDS) >= 50:
                try:
                    await u_bot.delete_messages(chat_id, DUPLICATE_IDS)
                    deleted += len(DUPLICATE_IDS)
                    DUPLICATE_IDS = []
                    await asyncio.sleep(1.5) # Anti-Flood
                except Exception as e:
                    logger.error(f"Delete Error: {e}")

        # Final Cleanup for remaining IDs
        if DUPLICATE_IDS:
            await u_bot.delete_messages(chat_id, DUPLICATE_IDS)
            deleted += len(DUPLICATE_IDS)

        final_status = "✅ <b>Cleaning Completed!</b>" if not temp.CANCEL.get(user_id) else "❌ <b>Task Cancelled!</b>"
        
        await sts_msg.edit(
            f"{final_status}\n\n"
            f"<b>📊 Final Stats:</b>\n"
            f"• Total Scanned: <code>{total}</code>\n"
            f"• Duplicates Removed: <code>{deleted}</code>\n\n"
            f"<i>Channel is now 100% unique!</i>", 
            reply_markup=get_btns(True)
        )

    except Exception as e:
        logger.error(f"Unequify Error: {e}")
        await sts_msg.edit(f"<b>❌ Engine Error:</b>\n<code>{e}</code>")
    
    finally:
        temp.lock[user_id] = False
        if u_bot and u_bot.is_connected:
            await u_bot.stop()
