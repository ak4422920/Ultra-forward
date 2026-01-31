import re, asyncio
from database import db
from config import temp
from .test import CLIENT , start_clone_bot
from translation import Translation
from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CLIENT = CLIENT()

COMPLETED_BTN = InlineKeyboardMarkup(
   [
      [InlineKeyboardButton('💟 Adult Channel 💟', url='https://t.me/PurelySin')],
      [InlineKeyboardButton('💠 Update Channel 💠', url='https://t.me/AkMovieVerse')]
   ]
)

CANCEL_BTN = InlineKeyboardMarkup([[InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', 'terminate_frwd')]])

@Client.on_message(filters.command("unequify") & filters.private)
async def unequify(client, message):
   user_id = message.from_user.id
   temp.CANCEL[user_id] = False
   
   if temp.lock.get(user_id) and str(temp.lock.get(user_id))=="True":
      return await message.reply("**ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴜɴᴛɪʟʟ ᴘʀᴇᴠɪᴏᴜs ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ.**")
      
   _bot = await db.get_bot(user_id)
   if not _bot:
      return await message.reply("<code>__**You didn't added any bot. Please add a bot using /settings !**__</code>")
      
   msg = await message.reply_text("Forward the last message of the channel (where you want to delete duplicates) or send the channel's ID.")
   fromid = await client.ask(message.chat.id, "Waiting for response...")
   
   if fromid.text.startswith('/'):
      return await message.reply(Translation.CANCEL)
      
   if fromid.forward_from_chat:
      chat_id = fromid.forward_from_chat.id
   else:
      try:
         chat_id = int(fromid.text)
      except:
         return await message.reply("Invalid ID! Please send a valid channel ID.")

   temp.lock[user_id] = True
   sts = await message.reply_text(Translation.DUPLICATE_TEXT.format(0, 0, "ᴘʀᴏɢʀᴇssɪɴɢ"), reply_markup=CANCEL_BTN)
   
   bot = Client(
      name=f"unequify_{user_id}",
      api_id=Config.API_ID,
      api_hash=Config.API_HASH,
      bot_token=_bot['token']
   )
   
   try:
      await bot.start()
      MESSAGES = []
      DUPLICATE = []
      total = 0
      deleted = 0
      
      # Searching for documents to find duplicates
      async for message in bot.search_messages(chat_id=chat_id, filter="document"):
         if temp.CANCEL.get(user_id) == True:
            await sts.edit(Translation.DUPLICATE_TEXT.format(total, deleted, "ᴄᴀɴᴄᴇʟʟᴇᴅ"), reply_markup=COMPLETED_BTN)
            await bot.stop()
            temp.lock[user_id] = False
            return
            
         file = message.document
         # Unique file identification logic
         file_id = file.file_unique_id 
         
         if file_id in MESSAGES:
            DUPLICATE.append(message.id)
         else:
            MESSAGES.append(file_id)
            
         total += 1
         
         if total % 100 == 0:
            await sts.edit(Translation.DUPLICATE_TEXT.format(total, deleted, "ᴘʀᴏɢʀᴇssɪɴɢ"), reply_markup=CANCEL_BTN)
            
         if len(DUPLICATE) >= 100:
            await bot.delete_messages(chat_id, DUPLICATE)
            deleted += len(DUPLICATE)
            await sts.edit(Translation.DUPLICATE_TEXT.format(total, deleted, "ᴘʀᴏɢʀᴇssɪɴɢ"), reply_markup=CANCEL_BTN)
            DUPLICATE = []
            
      if DUPLICATE:
         await bot.delete_messages(chat_id, DUPLICATE)
         deleted += len(DUPLICATE)
         
      await sts.edit(Translation.DUPLICATE_TEXT.format(total, deleted, "ᴄᴏᴍᴘʟᴇᴛᴇᴅ"), reply_markup=COMPLETED_BTN)
      
   except Exception as e:
      await message.reply(f"Error: {e}")
   finally:
      temp.lock[user_id] = False
      if bot.is_connected:
         await bot.stop()
