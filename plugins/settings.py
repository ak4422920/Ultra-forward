import asyncio 
from database import db
from translation import Translation
from pyrogram import Client, filters
from .test import get_configs, update_configs, CLIENT, parse_buttons
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CLIENT = CLIENT()

#Dont Remove My Credit @Silicon_Bot_Update 
#This Repo Is By @Silicon_Official 
# For Any Kind Of Error Ask Us In Support Group @Silicon_Botz 

@Client.on_message(filters.command('settings'))
async def settings(client, message):
   await message.delete()
   await message.reply_text(
     "<b>⚙️ cʜᴀɴɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ᴀs ʏᴏᴜʀ ᴡɪsʜ.</b>",
     reply_markup=main_buttons()
     )
    
@Client.on_callback_query(filters.regex(r'^settings'))
async def settings_query(bot, query):
  user_id = query.from_user.id
  # Fixing the split logic to handle multiple '#'
  data_split = query.data.split("#")
  type = data_split[1]
  buttons = [[InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data="settings#main")]]
  
  if type=="main":
     await query.message.edit_text(
       "<b>⚙️ cʜᴀɴɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ᴀs ʏᴏᴜʀ ᴡɪsʜ.</b>",
       reply_markup=main_buttons())

  # --- Problem #08: Stats Logic ---
  elif type == "stats":
     users, bots = await db.total_users_bots_count()
     channels = await db.total_channels()
     await query.message.edit_text(
        f"<b>📊 ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs</b>\n\n👤 ᴜsᴇʀs: {users}\n🤖 ᴡᴏʀᴋᴇʀ ʙᴏᴛs: {bots}\n📡 ᴄʜᴀɴɴᴇʟs: {channels}",
        reply_markup=InlineKeyboardMarkup(buttons))

  # --- Problem #09: Donate Logic ---
  elif type == "donate":
     await query.message.edit_text(
        "<b>💖 ᴅᴏɴᴀᴛᴇ ᴛᴏ sᴜᴘᴘᴏʀᴛ</b>\n\nɪғ ʏᴏᴜ ʟɪᴋᴇ ᴛʜɪs ʙᴏᴛ, ᴄᴏɴsɪᴅᴇʀ ᴅᴏɴᴀᴛɪɴɢ ᴛᴏ ᴋᴇᴇᴘ ɪᴛ ᴀʟɪᴠᴇ.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ", url="https://t.me/Silicon_Official")], buttons[0]]))
       
  elif type=="bots":
     _bot = await db.get_bot(user_id)
     btn = [] 
     if _bot:
        btn.append([InlineKeyboardButton(_bot['name'], callback_data="settings#editbot")])
     else:
        btn.append([InlineKeyboardButton('✚ ᴀᴅᴅ ʙᴏᴛ ✚', callback_data="settings#addbot")])
     btn.append([InlineKeyboardButton('✚ ᴀᴅᴅ ᴜsᴇʀ ʙᴏᴛ ✚', callback_data="settings#adduserbot")])
     btn.append([InlineKeyboardButton('✚ ʟᴏɢɪɴ ᴜsᴇʀ ʙᴏᴛ ✚', callback_data="settings#addlogin")])
     btn.append([InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data="settings#main")])
     await query.message.edit_text("<b>🤖 ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ʙᴏᴛs</b>", reply_markup=InlineKeyboardMarkup(btn))
  
  elif type in ["addbot", "addlogin", "adduserbot"]:
     await query.message.delete()
     if type == "addbot": await CLIENT.add_bot(bot, query.message)
     elif type == "addlogin": await CLIENT.add_login(bot, query.message)
     elif type == "adduserbot": await CLIENT.add_session(bot, query.message)
     await bot.send_message(user_id, "<b>ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ! ✅</b>", reply_markup=InlineKeyboardMarkup(buttons))
      
  elif type=="channels":
     channels = await db.get_user_channels(user_id)
     btn = [[InlineKeyboardButton(f"{ch['title']}", callback_data=f"settings#editchannels_{ch['chat_id']}")] for ch in channels]
     btn.append([InlineKeyboardButton('✚ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ ✚', callback_data="settings#addchannel")])
     btn.append([InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data="settings#main")])
     await query.message.edit_text("<b>📡 ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟs</b>", reply_markup=InlineKeyboardMarkup(btn))

  # --- Keyword Replacements Menu ---
  elif type == "replacements":
     configs = await get_configs(user_id)
     words = configs.get('replace_words', {})
     text = "<b><u>🔀 ᴋᴇʏᴡᴏʀᴅ ʀᴇᴘʟᴀᴄᴇᴍᴇɴᴛ</u></b>\n\n"
     for old, new in words.items():
         text += f"• <code>{old}</code> ➜ <code>{new if new else '[REMOVED]'}</code>\n"
     if not words: text += "<i>No replacements set.</i>"
     btn = [[InlineKeyboardButton('✚ ᴀᴅᴅ', callback_data="settings#add_rep")], [InlineKeyboardButton('🗑️ ᴄʟᴇᴀʀ', callback_data="settings#clear_rep")], buttons[0]]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

  elif type == "add_rep":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>Format:</b> <code>OldWord : NewWord</code>")
     if ask.text != "/cancel" and ":" in ask.text:
         old, new = [i.strip() for i in ask.text.split(":", 1)]
         configs = await get_configs(user_id)
         words = configs.get('replace_words', {})
         words[old] = new
         await update_configs(user_id, 'replace_words', words)
         await bot.send_message(user_id, "✅ Added!", reply_markup=InlineKeyboardMarkup(buttons))

  # --- Thumbnail Menu ---
  elif type == "thumbnail":
     configs = await get_configs(user_id)
     thumb = configs.get('thumbnail')
     text = f"<b>🖼️ ᴛʜᴜᴍʙɴᴀɪʟ sᴛᴀᴛᴜs:</b> {'✅ Set' if thumb else '❌ Not Set'}"
     btn = [[InlineKeyboardButton('🖼️ sᴇᴛ', callback_data="settings#set_thumb")]]
     if thumb: btn.append([InlineKeyboardButton('🗑️ ᴅᴇʟᴇᴛᴇ', callback_data="settings#del_thumb")])
     btn.append(buttons[0])
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

  elif type == "set_thumb":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>Send photo for thumbnail.</b>")
     if ask.photo:
         await update_configs(user_id, 'thumbnail', ask.photo.file_id)
         await bot.send_message(user_id, "✅ Thumbnail Set!", reply_markup=InlineKeyboardMarkup(buttons))

  # --- Backup Menu ---
  elif type == "backup":
     configs = await get_configs(user_id)
     backup = configs.get('admin_backup')
     text = f"<b>📡 ʙᴀᴄᴋᴜᴘ ᴄʜᴀɴɴᴇʟ:</b> <code>{backup if backup else 'Not Set'}</code>"
     btn = [[InlineKeyboardButton('📡 sᴇᴛ', callback_data="settings#set_backup")], buttons[0]]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

  elif type == "set_backup":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>Forward message from backup channel.</b>")
     if ask.forward_from_chat:
         await update_configs(user_id, 'admin_backup', ask.forward_from_chat.id)
         await bot.send_message(user_id, "✅ Backup Channel Set!", reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type=="caption":
     data = await get_configs(user_id)
     btn = [[InlineKeyboardButton('🖋️ Edit' if data['caption'] else '✚ Add', callback_data="settings#addcaption")], buttons[0]]
     await query.message.edit_text("<b>📝 ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ</b>", reply_markup=InlineKeyboardMarkup(btn))
                              
  elif type=="filters":
     await query.message.edit_text("<b>💠 CUSTOM FILTERS</b>", reply_markup=await filters_buttons(user_id))

  elif type=="nextfilters":
     await query.edit_message_reply_markup(reply_markup=await next_filters_buttons(user_id))
   
  elif "updatefilter" in type:
     i, key, val = type.split('-')
     new_val = False if val == "True" else True
     configs = await get_configs(user_id)
     if key in ["forward_tag", "duplicate", "protect"]:
         await update_configs(user_id, key, new_val)
     else:
         f = configs.get('filters', {})
         f[key] = new_val
         await update_configs(user_id, 'filters', f)
     
     markup = await next_filters_buttons(user_id) if key in ['poll', 'protect'] else await filters_buttons(user_id)
     await query.edit_message_reply_markup(reply_markup=markup)
   
  elif type == "file_size":
    settings = await get_configs(user_id)
    size = settings.get('file_size', 0)
    await query.message.edit_text(f'<b><u>SIZE LIMIT</b></u>\n\nStatus: `{size} MB`', reply_markup=size_button(size))
  
  elif type == "update_size":
    size = int(data_split[2])
    await update_configs(user_id, 'file_size', size)
    await query.message.edit_text(f'<b><u>SIZE LIMIT</b></u>\n\nUpdated: `{size} MB`', reply_markup=size_button(size))

  elif type == "get_extension":
    extensions = (await get_configs(user_id)).get('extension', [])
    btn = extract_btn(extensions)
    btn.append([InlineKeyboardButton('✚ ᴀᴅᴅ', 'settings#add_extension'), InlineKeyboardButton('ʀᴇᴍᴏᴠᴇ', 'settings#rmve_all_extension')])
    btn.append(buttons[0])
    await query.message.edit_text('<b><u>EXTENSIONS</u></b>', reply_markup=InlineKeyboardMarkup(btn))

  elif type == "get_keyword":
    keywords = (await get_configs(user_id)).get('keywords', [])
    btn = extract_btn(keywords)
    btn.append([InlineKeyboardButton('✚ ᴀᴅᴅ', 'settings#add_keyword'), InlineKeyboardButton('ʀᴇᴍᴏᴠᴇ', 'settings#rmve_all_keyword')])
    btn.append(buttons[0])
    await query.message.edit_text('<b><u>KEYWORDS</u></b>', reply_markup=InlineKeyboardMarkup(btn))

# ================= UI HELPERS ================= #

def main_buttons():
  buttons = [
    [InlineKeyboardButton('🤖 ʙᴏᴛs', 'settings#bots'), InlineKeyboardButton('📡 ᴄʜᴀɴɴᴇʟs', 'settings#channels')],
    [InlineKeyboardButton('🖋️ ᴄᴀᴘᴛɪᴏɴ', 'settings#caption'), InlineKeyboardButton('🖼️ ᴛʜᴜᴍʙɴᴀɪʟ', 'settings#thumbnail')],
    [InlineKeyboardButton('🔀 ʀᴇᴘʟᴀᴄᴇ ᴡᴏʀᴅs', 'settings#replacements'), InlineKeyboardButton('📡 ʙᴀᴄᴋᴜᴘ', 'settings#backup')],
    [InlineKeyboardButton('🕵️ ғɪʟᴛᴇʀs', 'settings#filters'), InlineKeyboardButton('📊 sᴛᴀᴛs', 'settings#stats')],
    [InlineKeyboardButton('💖 ᴅᴏɴᴀᴛᴇ', 'settings#donate'), InlineKeyboardButton('🧪 ᴇxᴛʀᴀ', 'settings#nextfilters')],
    [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='help')]
  ]
  return InlineKeyboardMarkup(buttons)

def size_button(size):
  return InlineKeyboardMarkup([
    [InlineKeyboardButton('+10', f'settings#update_size#{size + 10}'), InlineKeyboardButton('-10', f'settings#update_size#{max(0, size - 10)}')],
    [InlineKeyboardButton('+50', f'settings#update_size#{size + 50}'), InlineKeyboardButton('-50', f'settings#update_size#{max(0, size - 50)}')],
    [InlineKeyboardButton('↩ Back', "settings#nextfilters")]
  ])

def extract_btn(datas):
    btn = []
    if datas:
       for i in range(0, len(datas), 2):
          row = [InlineKeyboardButton(datas[i], f"settings#alert_{datas[i]}")]
          if i+1 < len(datas): row.append(InlineKeyboardButton(datas[i+1], f"settings#alert_{datas[i+1]}"))
          btn.append(row)
    return btn 

async def filters_buttons(user_id):
  filter = await get_configs(user_id)
  f = filter['filters']
  def icon(v): return "✅" if v else "❌"
  buttons = [
    [InlineKeyboardButton('🏷️ ғᴏʀᴡᴀʀᴅ ᴛᴀɢ', 'none'), InlineKeyboardButton(icon(filter["forward_tag"]), f'settings#updatefilter-forward_tag-{filter["forward_tag"]}')],
    [InlineKeyboardButton('🖍️ ᴛᴇxᴛ', 'none'), InlineKeyboardButton(icon(f["text"]), f'settings#updatefilter-text-{f["text"]}')],
    [InlineKeyboardButton('🎞️ ᴠɪᴅᴇᴏs', 'none'), InlineKeyboardButton(icon(f["video"]), f'settings#updatefilter-video-{f["video"]}')],
    [InlineKeyboardButton('📷 ᴘʜᴏᴛᴏs', 'none'), InlineKeyboardButton(icon(f["photo"]), f'settings#updatefilter-photo-{f["photo"]}')],
    [InlineKeyboardButton('• ʙᴀᴄᴋ', "settings#main")]
  ]
  return InlineKeyboardMarkup(buttons) 

async def next_filters_buttons(user_id):
  filter = await get_configs(user_id)
  f = filter['filters']
  def icon(v): return "✅" if v else "❌"
  buttons = [
    [InlineKeyboardButton('📊 ᴘᴏʟʟ', 'none'), InlineKeyboardButton(icon(f["poll"]), f'settings#updatefilter-poll-{f["poll"]}')],
    [InlineKeyboardButton('🔒 sᴇᴄᴜʀᴇ ᴍᴇss', 'none'), InlineKeyboardButton(icon(filter["protect"]), f'settings#updatefilter-protect-{filter["protect"]}')],
    [InlineKeyboardButton('📏 sɪᴢᴇ ʟɪᴍɪᴛ', 'settings#file_size'), InlineKeyboardButton('▶️ ᴅᴜᴘʟɪᴄᴀᴛᴇ', f'settings#updatefilter-duplicate-{filter["duplicate"]}')],
    [InlineKeyboardButton('💾 ᴇxᴛᴇɴsɪᴏɴ', 'settings#get_extension'), InlineKeyboardButton('♦️ ᴋᴇʏᴡᴏʀᴅ', 'settings#get_keyword')],
    [InlineKeyboardButton('• ʙᴀᴄᴋ', "settings#main")]
  ]
  return InlineKeyboardMarkup(buttons)
