import re
import asyncio
from database import db
from config import temp
from .test import CLIENT, start_clone_bot
from translation import Translation
from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CLIENT_OBJ = CLIENT()

# UI Buttons (Credits Retained)
COMPLETED_BTN = InlineKeyboardMarkup([[InlineKeyboardButton('💠 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/Silicon_Official')]])
CANCEL_BTN = InlineKeyboardMarkup([[InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', 'terminate_frwd')]])

@Client.on_message(filters.command("unequify") & filters.private)
async def unequify_handler(bot, message):
    user_id = message.from_user.id
    temp.CANCEL[user_id] = False
    
    # 1. 🔒 Lock Check (Problem #04 Fixed)
    if temp.lock.get(user_id):
        return await message.reply("**ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴜɴᴛɪʟʟ ᴘʀᴇᴠɪᴏᴜs ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇ**")
    
    # 2. 🤖 Userbot Requirement (#10)
    _bot = await db.get_bot(user_id)
    if not _bot or _bot.get('is_bot'):
        return await message.reply("<b>Need Userbot to do this process. Please add a Userbot using /settings</b>")
    
    # 3. 📑 Input Parsing (Link or Forward)
    target = await bot.ask(user_id, text="**Forward a message from target chat or send message link.**\n/cancel - `Stop`")
    if target.text and target.text.startswith("/"): return await message.reply("❌ **Cancelled!**")
    
    chat_id = None
    if target.text:
        # Regex for all types of Telegram links
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(target.text.replace("?single", ""))
        if match:
            chat_id = match.group(4)
            if chat_id.isnumeric(): chat_id = int(("-100" + chat_id))
    elif target.forward_from_chat:
        chat_id = target.forward_from_chat.id
    
    if not chat_id: return await message.reply("**Invalid Input!** Link ya forward sahi se bhejein.")

    # 4. ✅ Confirmation Step
    confirm = await bot.ask(user_id, text=f"Target Chat: `{chat_id}`\n\n**Send /yes to start or /no to cancel.**")
    if confirm.text.lower() != '/yes': return await confirm.reply("❌ **Process Stopped.**")
    
    sts_msg = await confirm.reply("`Starting Userbot and verifying access...`")
    
    # 5. 🚀 The Engine (Try-Finally Block for Safety)
    u_bot = None
    try:
        u_bot = await start_clone_bot(CLIENT_OBJ.client(_bot))
        temp.lock[user_id] = True
        
        MESSAGES_SET = set() # Unique Fingerprints
        DUPLICATE_IDS = []
        total, deleted = 0, 0

        # Scanning all media (get_chat_history is more reliable than search)
        async for msg in u_bot.get_chat_history(chat_id):
            if temp.CANCEL.get(user_id): break
            
            total += 1
            if msg.media:
                # Digital Fingerprint check
                f_id = getattr(getattr(msg, msg.media.value, None), 'file_unique_id', None)
                if f_id:
                    if f_id in MESSAGES_SET:
                        DUPLICATE_IDS.append(msg.id)
                    else:
                        MESSAGES_SET.add(f_id)
            
            # Batch UI Update
            if total % 100 == 0:
                await sts_msg.edit(f"🔍 **Scanning:** `{total}`\n🗑️ **Found:** `{len(DUPLICATE_IDS) + deleted}`", reply_markup=CANCEL_BTN)
            
            # Batch Deletion to avoid FloodWait
            if len(DUPLICATE_IDS) >= 50:
                await u_bot.delete_messages(chat_id, DUPLICATE_IDS)
                deleted += len(DUPLICATE_IDS)
                DUPLICATE_IDS = []

        # Final Cleanup
        if DUPLICATE_IDS:
            await u_bot.delete_messages(chat_id, DUPLICATE_IDS)
            deleted += len(DUPLICATE_IDS)

        final_text = "✅ **Process Completed!**" if not temp.CANCEL.get(user_id) else "❌ **Process Cancelled!**"
        await sts_msg.edit(f"{final_text}\n\nTotal Scanned: `{total}`\nDuplicates Removed: `{deleted}`", reply_markup=COMPLETED_BTN)

    except Exception as e:
        await sts_msg.edit(f"❌ **Error:** `{e}`")
    
    finally:
        # 🔓 Lock always opens
        temp.lock[user_id] = False
        if u_bot: await u_bot.stop()
