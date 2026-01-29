import re
import asyncio
from database import db
from config import temp
from .test import CLIENT , start_clone_bot
from translation import Translation
from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CLIENT = CLIENT()

# Modern Buttons
COMPLETED_BTN = InlineKeyboardMarkup(
   [
      [InlineKeyboardButton('💠 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/AkMovieVerse')]
   ]
)

CANCEL_BTN = InlineKeyboardMarkup([[InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', 'terminate_frwd')]])

@Client.on_message(filters.command("unequify") & filters.private)
async def unequify(client, message):
   user_id = message.from_user.id
   temp.CANCEL[user_id] = False
   
   if temp.lock.get(user_id) and str(temp.lock.get(user_id))=="True":
      return await message.reply("**ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴜɴᴛɪʟʟ ᴘʀᴇᴠɪᴏᴜs ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇ**")
   
   _bot = await db.get_bot(user_id)
   if not _bot or _bot['is_bot']:
      return await message.reply("<b>Need Userbot to do this process. Please add a Userbot using /settings</b>")
   
   target = await client.ask(user_id, text="**Forward the last message from target chat or send last message link.**\n/cancel - `cancel this process`")
   
   if target.text.startswith("/"):
      return await message.reply("**Process Cancelled !**")
   
   chat_id = None
   if target.text:
      regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
      match = regex.match(target.text.replace("?single", ""))
      if not match:
         return await message.reply('**Invalid Link**')
      
      chat_id = match.group(4)
      if chat_id.isnumeric():
         chat_id = int(("-100" + chat_id))
   elif target.forward_from_chat:
      chat_id = target.forward_from_chat.id
   else:
      return await message.reply_text("**Invalid Input!**")

   confirm = await client.ask(user_id, text="**Send /yes to start the process and /no to cancel.**")
   if confirm.text.lower() == '/no':
      return await confirm.reply("**Process Cancelled !**")
   
   sts = await confirm.reply("`Processing Duplicate Files...`")
   
   try:
      bot = await start_clone_bot(CLIENT.client(_bot))
   except Exception as e:
      return await sts.edit(f"**Bot Start Error:** `{e}`")

   try:
       test_msg = await bot.send_message(chat_id, text="`Duplicate Check Starting...`")
       await test_msg.delete()
   except:
       await sts.edit(f"**Error:** Please make your Userbot admin in target chat.")
       return await bot.stop()

   MESSAGES_SET = set() # Faster lookup
   DUPLICATE_IDS = []
   total = 0
   deleted = 0
   temp.lock[user_id] = True

   try:
     # Modern block-style progress tracking
     async for msg in bot.search_messages(chat_id=chat_id, filter="document"):
        if temp.CANCEL.get(user_id) == True:
           await sts.edit("<b>❌ Process Cancelled by User.</b>", reply_markup=COMPLETED_BTN)
           temp.lock[user_id] = False
           return await bot.stop()

        file = msg.document
        # Using file_unique_id for perfect duplicate detection
        file_unique_id = file.file_unique_id 
        
        if file_unique_id in MESSAGES_SET:
           DUPLICATE_IDS.append(msg.id)
        else:
           MESSAGES_SET.add(file_unique_id)
        
        total += 1
        
        # UI Update
        if total % 100 == 0:
           await sts.edit(f"🔍 **Scanning:** `{total}` files\n🗑️ **Duplicates Found:** `{len(DUPLICATE_IDS) + deleted}`", reply_markup=CANCEL_BTN)
        
        # Delete in batches to avoid flood
        if len(DUPLICATE_IDS) >= 100:
           await bot.delete_messages(chat_id, DUPLICATE_IDS)
           deleted += len(DUPLICATE_IDS)
           DUPLICATE_IDS = []
           await sts.edit(f"🔍 **Scanning:** `{total}` files\n🗑️ **Deleted:** `{deleted}`", reply_markup=CANCEL_BTN)

     # Final batch delete
     if DUPLICATE_IDS:
        await bot.delete_messages(chat_id, DUPLICATE_IDS)
        deleted += len(DUPLICATE_IDS)

   except Exception as e:
       temp.lock[user_id] = False 
       await sts.edit(f"**ERROR:** `{e}`")
       return await bot.stop()

   temp.lock[user_id] = False
   await sts.edit(f"✅ **Process Completed!**\n\nTotal Scanned: `{total}`\nDuplicates Removed: `{deleted}`", reply_markup=COMPLETED_BTN)
   await bot.stop()
