import asyncio 
from database import db
from translation import Translation
from pyrogram import Client, filters
from .test import get_configs, update_configs, CLIENT, parse_buttons
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CLIENT = CLIENT()

@Client.on_message(filters.command('settings') & filters.private)
async def settings(client, message):
   await message.reply_text(
     "<b>⚙️ ᴄʜᴀɴɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ᴀs ʏᴏᴜʀ ᴡɪsʜ.</b>",
     reply_markup=main_buttons()
   )

@Client.on_callback_query(filters.regex(r'^settings'))
async def settings_query(bot, query):
  user_id = query.from_user.id
  data_split = query.data.split("#")
  type = data_split[1]
  
  # Default Back Button
  back_main = [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data="settings#main")]
  back_btn_markup = InlineKeyboardMarkup([back_main])

  if type == "main":
     await query.message.edit_text(
       "<b>⚙️ ᴄʜᴀɴɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ᴀs ʏᴏᴜʀ ᴡɪsʜ.</b>",
       reply_markup=main_buttons())

  # --- Bot & Userbot Management ---
  elif type == "bots":
     _bot = await db.get_bot(user_id)
     buttons = []
     if _bot:
        buttons.append([InlineKeyboardButton(f"🤖 {_bot['name']}", callback_data="settings#editbot")])
        buttons.append([InlineKeyboardButton('✚ ᴀᴅᴅ ᴜsᴇʀ ʙᴏᴛ', callback_data="settings#adduserbot")])
        buttons.append([InlineKeyboardButton('✚ ʟᴏɢɪɴ ᴜsᴇʀ ʙᴏᴛ', callback_data="settings#addlogin")])
     else:
        buttons.append([InlineKeyboardButton('✚ ᴀᴅᴅ ʙᴏᴛ', callback_data="settings#addbot")])
        buttons.append([InlineKeyboardButton('✚ ᴀᴅᴅ ᴜsᴇʀ ʙᴏᴛ', callback_data="settings#adduserbot")])
        buttons.append([InlineKeyboardButton('✚ ʟᴏɢɪɴ ᴜsᴇʀ ʙᴏᴛ', callback_data="settings#addlogin")])
     buttons.append(back_main)
     await query.message.edit_text("<b>🤖 ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ʙᴏᴛs</b>", reply_markup=InlineKeyboardMarkup(buttons))

  elif type in ["addbot", "addlogin", "adduserbot"]:
     await query.message.delete()
     if type == "addbot": await CLIENT.add_bot(bot, query)
     elif type == "addlogin": await CLIENT.add_login(bot, query)
     elif type == "adduserbot": await CLIENT.add_session(bot, query)
     await bot.send_message(user_id, "<b>ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ! ✅</b>", reply_markup=back_btn_markup)

  elif type == "editbot": 
     _bot = await db.get_bot(user_id)
     TEXT_DETAIL = Translation.BOT_DETAILS if _bot['is_bot'] else Translation.USER_DETAILS
     buttons = [[InlineKeyboardButton('❌ ʀᴇᴍᴏᴠᴇ ❌', callback_data="settings#removebot")], [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data="settings#bots")]]
     await query.message.edit_text(TEXT_DETAIL.format(_bot['name'], _bot['id'], _bot['username']), reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "removebot":
     await db.remove_bot(user_id)
     await query.message.edit_text("<b>ʙᴏᴛ sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ ✅</b>", reply_markup=back_btn_markup)

  # --- Target Channels ---
  elif type == "channels":
     channels = await db.get_user_channels(user_id)
     buttons = [[InlineKeyboardButton(f"📁 {ch['title']}", callback_data=f"settings#editchannels_{ch['chat_id']}")] for ch in channels]
     buttons.append([InlineKeyboardButton('✚ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ', callback_data="settings#addchannel")])
     buttons.append(back_main)
     await query.message.edit_text("<b>ʏᴏᴜʀ ᴛᴀʀɢᴇᴛ ᴄʜᴀɴɴᴇʟs</b>", reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "addchannel":
     await query.message.delete()
     try:
         prompt = await bot.send_message(user_id, "<b>ғᴏʀᴡᴀʀᴅ ᴀ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴛᴀʀɢᴇᴛ ᴄʜᴀɴɴᴇʟ.\n/cancel - To Cancel.</b>")
         chat_ids = await bot.listen(chat_id=user_id, timeout=300)
         if chat_ids.text == "/cancel": return
         if not chat_ids.forward_date:
            return await bot.send_message(user_id, "❌ Not a forwarded message!", reply_markup=back_btn_markup)
         
         chat_id = chat_ids.forward_from_chat.id
         title = chat_ids.forward_from_chat.title
         username = f"@{chat_ids.forward_from_chat.username}" if chat_ids.forward_from_chat.username else "Private"
         
         added = await db.add_channel(user_id, chat_id, title, username)
         await bot.send_message(user_id, "<b>✅ Added!</b>" if added else "<b>Already added!</b>", reply_markup=back_btn_markup)
     except: pass

  # --- Point #1: Keyword Replacement ---
  elif type == "replacements":
     configs = await get_configs(user_id)
     words = configs.get('replace_words', {})
     text = "<b><u>🔀 ᴋᴇʏᴡᴏʀᴅ ʀᴇᴘʟᴀᴄᴇᴍᴇɴᴛ</u></b>\n\n"
     if words:
         for old, new in words.items():
             text += f"• <code>{old}</code> ➜ <code>{new if new else '[REMOVED]'}</code>\n"
     else:
         text += "<i>No replacements set.</i>"
     buttons = [[InlineKeyboardButton('✚ ᴀᴅᴅ ʀᴇᴘʟᴀᴄᴇᴍᴇɴᴛ', callback_data="settings#add_rep")], [InlineKeyboardButton('🗑️ ᴄʟᴇᴀʀ ᴀʟʟ', callback_data="settings#clear_rep")], back_main]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "add_rep":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>Send replacement in format:</b>\n<code>OldWord : NewWord</code>\n\n<i>To remove a word, use:</i>\n<code>OldWord : </code>")
     if ask.text != "/cancel" and ":" in ask.text:
         old, new = [i.strip() for i in ask.text.split(":", 1)]
         configs = await get_configs(user_id)
         words = configs.get('replace_words', {})
         words[old] = new
         await update_configs(user_id, 'replace_words', words)
         await bot.send_message(user_id, "✅ Added!", reply_markup=back_btn_markup)

  # --- Point #2: Thumbnail ---
  elif type == "thumbnail":
     configs = await get_configs(user_id)
     thumb = configs.get('thumbnail')
     buttons = [[InlineKeyboardButton('🖼️ sᴇᴛ ᴛʜᴜᴍʙɴᴀɪʟ', callback_data="settings#set_thumb")]]
     if thumb: buttons.append([InlineKeyboardButton('🗑️ ᴅᴇʟᴇᴛᴇ', callback_data="settings#del_thumb")])
     buttons.append(back_main)
     await query.message.edit_text(f"<b>🖼️ ᴛʜᴜᴍʙɴᴀɪʟ sᴛᴀᴛᴜs:</b> {'✅ Set' if thumb else '❌ Not Set'}", reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "set_thumb":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>Send the photo for thumbnail.</b>")
     if ask.photo:
         await update_configs(user_id, 'thumbnail', ask.photo.file_id)
         await bot.send_message(user_id, "✅ Thumbnail Set!", reply_markup=back_btn_markup)

  # --- Point #3: Admin Backup ---
  elif type == "backup":
     configs = await get_configs(user_id)
     backup = configs.get('admin_backup')
     buttons = [[InlineKeyboardButton('📡 sᴇᴛ ʙᴀᴄᴋᴜᴘ ᴄʜᴀɴɴᴇʟ', callback_data="settings#set_backup")]]
     if backup: buttons.append([InlineKeyboardButton('🗑️ ʀᴇᴍᴏᴠᴇ', callback_data="settings#del_backup")])
     buttons.append(back_main)
     await query.message.edit_text(f"<b>📡 ʙᴀᴄᴋᴜᴘ ᴄʜᴀɴɴᴇʟ ID:</b> <code>{backup if backup else 'Not Set'}</code>", reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "set_backup":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>Forward a message from backup channel.</b>")
     if ask.forward_from_chat:
         await update_configs(user_id, 'admin_backup', ask.forward_from_chat.id)
         await bot.send_message(user_id, "✅ Backup Channel Set!", reply_markup=back_btn_markup)

  # --- Existing Caption Logic ---
  elif type=="caption":
     data = await get_configs(user_id)
     cap = data['caption']
     buttons = [[InlineKeyboardButton('🖋️ Edit' if cap else '✚ Add', callback_data="settings#addcaption")], back_main]
     await query.message.edit_text("<b>📝 ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ sᴇᴛᴛɪɴɢs</b>", reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "addcaption":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>Send Custom Caption.</b>\nFillings: <code>{filename}</code>, <code>{size}</code>, <code>{caption}</code>")
     if ask.text != "/cancel":
         await update_configs(user_id, 'caption', ask.text)
         await bot.send_message(user_id, "✅ Caption Updated!", reply_markup=back_btn_markup)

# ================= UI & FILTER HELPERS ================= #

def main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('🤖 ʙᴏᴛs', callback_data='settings#bots'), InlineKeyboardButton('📡 ᴄʜᴀɴɴᴇʟs', callback_data='settings#channels')],
        [InlineKeyboardButton('📝 ᴄᴀᴘᴛɪᴏɴ', callback_data='settings#caption'), InlineKeyboardButton('🔘 ʙᴜᴛᴛᴏɴs', callback_data='settings#button')],
        [InlineKeyboardButton('🔀 ʀᴇᴘʟᴀᴄᴇ ᴡᴏʀᴅs', callback_data='settings#replacements')],
        [InlineKeyboardButton('🖼️ ᴛʜᴜᴍʙɴᴀɪʟ', callback_data='settings#thumbnail'), InlineKeyboardButton('📡 ʙᴀᴄᴋᴜᴘ', callback_data='settings#backup')],
        [InlineKeyboardButton('🔍 ғɪʟᴛᴇʀs', callback_data='settings#filters'), InlineKeyboardButton('📏 sɪᴢᴇ', callback_data='settings#file_size')],
        [InlineKeyboardButton('📂 ᴇxᴛ.', callback_data='settings#get_extension'), InlineKeyboardButton('🔑 ᴋᴇʏᴡᴏʀᴅs', callback_data='settings#get_keyword')],
    ])

async def filters_buttons(user_id):
    c = (await get_configs(user_id))['filters']
    btn = []
    for k, v in c.items():
        sym = "✅" if v else "❌"
        btn.append([InlineKeyboardButton(f"{k.capitalize()}: {sym}", callback_data=f"settings#updatefilter-{k}-{v}")])
    btn.append([InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data="settings#main")])
    return InlineKeyboardMarkup(btn)

def size_button(current):
    btn = [
        [InlineKeyboardButton('➖ 10', f'settings#update_size-{max(0, current-10)}'), InlineKeyboardButton(f'{current} MB', 'none'), InlineKeyboardButton('➕ 10', f'settings#update_size-{current+10}')],
        [InlineKeyboardButton('• ʙᴀᴄᴋ', 'settings#main')]
    ]
    return InlineKeyboardMarkup(btn)

def extract_btn(data, type):
    btn = []
    for i in range(0, len(data), 2):
        row = [InlineKeyboardButton(data[i], "none")]
        if i+1 < len(data): row.append(InlineKeyboardButton(data[i+1], "none"))
        btn.append(row)
    return btn
   
async def filters_buttons(user_id):
  filter = await get_configs(user_id)
  filters = filter['filters']
  buttons = [[
       InlineKeyboardButton('🏷️ ғᴏʀᴡᴀʀᴅ ᴛᴀɢ',
                    callback_data=f'settings_#updatefilter-forward_tag-{filter["forward_tag"]}'),
       InlineKeyboardButton('✅' if filter['forward_tag'] else '❌',
                    callback_data=f'settings#updatefilter-forward_tag-{filter["forward_tag"]}')
       ],[
       InlineKeyboardButton('🖍️ ᴛᴇxᴛ',
                    callback_data=f'settings_#updatefilter-text-{filters["text"]}'),
       InlineKeyboardButton('✅' if filters['text'] else '❌',
                    callback_data=f'settings#updatefilter-text-{filters["text"]}')
       ],[
       InlineKeyboardButton('📁 ᴅᴏᴄᴜᴍᴇɴᴛs',
                    callback_data=f'settings_#updatefilter-document-{filters["document"]}'),
       InlineKeyboardButton('✅' if filters['document'] else '❌',
                    callback_data=f'settings#updatefilter-document-{filters["document"]}')
       ],[
       InlineKeyboardButton('🎞️ ᴠɪᴅᴇᴏs',
                    callback_data=f'settings_#updatefilter-video-{filters["video"]}'),
       InlineKeyboardButton('✅' if filters['video'] else '❌',
                    callback_data=f'settings#updatefilter-video-{filters["video"]}')
       ],[
       InlineKeyboardButton('📷 ᴘʜᴏᴛᴏs',
                    callback_data=f'settings_#updatefilter-photo-{filters["photo"]}'),
       InlineKeyboardButton('✅' if filters['photo'] else '❌',
                    callback_data=f'settings#updatefilter-photo-{filters["photo"]}')
       ],[
       InlineKeyboardButton('🎧 ᴀᴜᴅɪᴏs',
                    callback_data=f'settings_#updatefilter-audio-{filters["audio"]}'),
       InlineKeyboardButton('✅' if filters['audio'] else '❌',
                    callback_data=f'settings#updatefilter-audio-{filters["audio"]}')
       ],[
       InlineKeyboardButton('🎤 ᴠᴏɪᴄᴇs',
                    callback_data=f'settings_#updatefilter-voice-{filters["voice"]}'),
       InlineKeyboardButton('✅' if filters['voice'] else '❌',
                    callback_data=f'settings#updatefilter-voice-{filters["voice"]}')
       ],[
       InlineKeyboardButton('🎭 ᴀɴɪᴍᴀᴛɪᴏɴs',
                    callback_data=f'settings_#updatefilter-animation-{filters["animation"]}'),
       InlineKeyboardButton('✅' if filters['animation'] else '❌',
                    callback_data=f'settings#updatefilter-animation-{filters["animation"]}')
       ],[
       InlineKeyboardButton('🃏 sᴛɪᴄᴋᴇʀs',
                    callback_data=f'settings_#updatefilter-sticker-{filters["sticker"]}'),
       InlineKeyboardButton('✅' if filters['sticker'] else '❌',
                    callback_data=f'settings#updatefilter-sticker-{filters["sticker"]}')
       ],[
       InlineKeyboardButton('▶️ sᴋɪᴘ ᴅᴜᴘʟɪᴄᴀᴛᴇ',
                    callback_data=f'settings_#updatefilter-duplicate-{filter["duplicate"]}'),
       InlineKeyboardButton('✅' if filter['duplicate'] else '❌',
                    callback_data=f'settings#updatefilter-duplicate-{filter["duplicate"]}')
       ],[
       InlineKeyboardButton('• ʙᴀᴄᴋ',
                    callback_data="settings#main")
       ]]
  return InlineKeyboardMarkup(buttons) 

async def next_filters_buttons(user_id):
  filter = await get_configs(user_id)
  filters = filter['filters']
  buttons = [[
       InlineKeyboardButton('📊 ᴘᴏʟʟ',
                    callback_data=f'settings_#updatefilter-poll-{filters["poll"]}'),
       InlineKeyboardButton('✅' if filters['poll'] else '❌',
                    callback_data=f'settings#updatefilter-poll-{filters["poll"]}')
       ],[
       InlineKeyboardButton('🔒 sᴇᴄᴜʀᴇ ᴍᴇssᴀɢᴇs',
                    callback_data=f'settings_#updatefilter-protect-{filter["protect"]}'),
       InlineKeyboardButton('✅' if filter['protect'] else '❌',
                    callback_data=f'settings#updatefilter-protect-{filter["protect"]}')
       ],[
       InlineKeyboardButton('🛑 sɪᴢᴇ ʟɪᴍɪᴛ',
                    callback_data='settings#file_size')
       ],[
       InlineKeyboardButton('💾 ᴇxᴛᴇɴsɪᴏɴ',
                    callback_data='settings#get_extension')
       ],[
       InlineKeyboardButton('♦️ ᴋᴇʏᴡᴏʀᴅ',
                    callback_data='settings#get_keyword')
       ],[
       InlineKeyboardButton('• ʙᴀᴄᴋ', 
                    callback_data="settings#main")
       ]]
  return InlineKeyboardMarkup(buttons) 
   
