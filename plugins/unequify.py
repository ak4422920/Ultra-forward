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
        fsub_link = getattr(Config, 'FORCE_SUB_CHANNEL', 'https://t.me/Silicon_Official')
        return InlineKeyboardMarkup([[InlineKeyboardButton('💠 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url=fsub_link)]])
    return InlineKeyboardMarkup([[InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', callback_data='terminate_frwd')]])

@Client.on_message(filters.command("unequify") & filters.private)
async def unequify_handler(bot, message):
    user_id = message.from_user.id
    temp.CANCEL[user_id] = False
    
    # 1. 🔒 Lock Check (Multi-tasking preventer)
    if temp.lock.get(user_id):
        return await message.reply("<b>❌ Error:</b> Pehle se ek task chal raha hai.")
    
    # 2. 🤖 Worker Check (Bot Token won't work for History Scan)
    _bot = await db.get_bot(user_id)
    if not _bot:
        return await message.reply("<b>⚠️ Worker Missing!</b>\n\nHistory scan karne ke liye ek Worker (Session String) zaroori hai.")

    # 3. 📑 Input Parsing
    target = await bot.ask(user_id, text="<b>❪ ᴜɴᴇǫᴜɪғʏ sᴇᴛᴜᴘ ❫</b>\n\nJis channel se duplicates saaf karne hain, uska link bhejein ya wahan se ek message forward karein.\n\n/cancel - Task rokne ke liye.")
    if not target.text or target.text.startswith("/"): 
        return await message.reply("❌ **Process Cancelled!**")
    
    # Chat ID Extraction Logic
    chat_id = None
    if target.forward_from_chat:
        chat_id = target.forward_from_chat.id
    else:
        try:
            input_data = target.text.split('/')[-1]
            chat = await bot.get_chat(input_data)
            chat_id = chat.id
        except: 
            return await message.reply("<b>❌ Invalid Link!</b> Sahi channel link bhejein.")

    # 4. ✅ Confirmation Prompt
    confirm = await bot.ask(user_id, text=f"<b>Target Chat:</b> <code>{chat_id}</code>\n\nKya aap pakka is channel se saare duplicates delete karna chahte hain?\n\n<b>Reply:</b> /yes ya /no")
    if not confirm.text or confirm.text.lower() != '/yes': 
        return await confirm.reply("❌ **Cleaning Aborted.**")
    
    sts_msg = await confirm.reply("<b>⚙️ Initializing Engine...</b>\n<i>Scanning power activate ho rahi hai.</i>")
    
    # 5. 🚀 The Cleaning Engine
    u_bot = None
    try:
        # Worker start karna
        u_bot = await start_clone_bot(CLIENT_OBJ.client(_bot))
        temp.lock[user_id] = True
        
        MESSAGES_SET = set() # Unique Digital Fingerprints store karega
        DUPLICATE_IDS = []
        total, deleted = 0, 0

        # 
        async for msg in u_bot.get_chat_history(chat_id):
            if temp.CANCEL.get(user_id): break
            
            total += 1
            if msg.media:
                # File unique ID check (Sabse accurate method)
                media_type = msg.media.value
                f_id = getattr(getattr(msg, media_type, None), 'file_unique_id', None)
                
                if f_id:
                    if f_id in MESSAGES_SET:
                        DUPLICATE_IDS.append(msg.id)
                    else:
                        MESSAGES_SET.add(f_id)
            
            # Progress Update (Every 100 messages)
            if total % 100 == 0:
                try:
                    await sts_msg.edit(
                        f"<b>🔍 Scanning History...</b>\n\n"
                        f"• Scanned: <code>{total}</code>\n"
                        f"• Duplicates Found: <code>{len(DUPLICATE_IDS) + deleted}</code>", 
                        reply_markup=get_btns()
                    )
                except: pass
            
            # Batch Deletion (Flood protection: 100 ka batch)
            if len(DUPLICATE_IDS) >= 100:
                try:
                    await u_bot.delete_messages(chat_id, DUPLICATE_IDS)
                    deleted += len(DUPLICATE_IDS)
                    DUPLICATE_IDS = []
                    await asyncio.sleep(2) # Anti-Flood Wait
                except Exception as e:
                    logger.error(f"Batch Delete Error: {e}")

        # Final Deletion (Bache huye IDs)
        if DUPLICATE_IDS:
            await u_bot.delete_messages(chat_id, DUPLICATE_IDS)
            deleted += len(DUPLICATE_IDS)

        final_status = "✅ <b>Cleaning Completed!</b>" if not temp.CANCEL.get(user_id) else "❌ <b>Task Cancelled!</b>"
        
        await sts_msg.edit(
            f"{final_status}\n\n"
            f"<b>📊 Final Stats:</b>\n"
            f"• Total Scanned: <code>{total}</code>\n"
            f"• Duplicates Removed: <code>{deleted}</code>", 
            reply_markup=get_btns(True)
        )

    except Exception as e:
        logger.error(f"Unequify Engine Error: {e}")
        await sts_msg.edit(f"<b>❌ Error:</b> <code>{e}</code>")
    
    finally:
        temp.lock[user_id] = False
        if u_bot and u_bot.is_connected:
            await u_bot.stop()
