import asyncio 
from database import db
from config import Config
from translation import Translation
from pyrogram import Client, filters
from .test import get_configs, update_configs, CLIENT, parse_buttons
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CLIENT_MGR = CLIENT()

@Client.on_message(filters.command('settings') & filters.private)
async def settings(client, message):
   await message.reply_text(
     "<b>⚙️ ꜰᴏʀᴡᴀʀᴅ ᴇʟɪᴛᴇ ᴠ3: ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ</b>\n\nNiche diye gaye buttons se apni forwarding preferences set karein.",
     reply_markup=main_buttons()
   )
    
@Client.on_callback_query(filters.regex(r'^settings'))
async def settings_query(bot, query):
  user_id = query.from_user.id
  data_split = query.data.split("#")
  type = data_split[1]
  back_btn = [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data="settings#main")]
  
  # --- MAIN MENU ---
  if type == "main":
     await query.message.edit_text(
       "<b>⚙️ ꜰᴏʀᴡᴀʀᴅ ᴇʟɪᴛᴇ ᴠ3: ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ</b>",
       reply_markup=main_buttons())

  # --- [FEATURE] SMART THUMBNAIL MENU ---
  elif type == "thumbnail":
     configs = await get_configs(user_id)
     thumb = configs.get('thumbnail')
     # Translation se dynamic warning uthana (with VPS limit)
     text = Translation.THUMBNAIL_HELP.format(limit=Config.THUMB_LIMIT)
     
     btn = [[InlineKeyboardButton('🖼️ Set Thumbnail', callback_data="settings#set_thumb")]]
     if thumb:
         btn.append([InlineKeyboardButton('🗑️ Delete Thumbnail', callback_data="settings#del_thumb")])
     btn.append(back_btn)
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

  elif type == "set_thumb":
     await query.message.delete()
     ask = await bot.ask(user_id, Translation.THUMB_MESS if hasattr(Translation, 'THUMB_MESS') else "<b>Bhai, thumbnail ki photo bhejein:</b>")
     if ask.photo:
         await update_configs(user_id, 'thumbnail', ask.photo.file_id)
         await bot.send_message(user_id, "✅ **Thumbnail Set!**\nAb aapka task automatically restricted limit par chalega.", reply_markup=InlineKeyboardMarkup([back_btn]))
     else:
         await bot.send_message(user_id, "❌ **Error:** Sirf photo bhejein.", reply_markup=InlineKeyboardMarkup([back_btn]))

  elif type == "del_thumb":
     await update_configs(user_id, 'thumbnail', None)
     await query.answer("Thumbnail Deleted! 🗑️", show_alert=True)
     await query.message.edit_text("✅ Thumbnail removed. Unlimited forwarding restored!", reply_markup=InlineKeyboardMarkup([back_btn]))

  # --- [FEATURE] KEYWORD MAPPER (REPLACEMENTS) ---
  elif type == "replacements":
     configs = await get_configs(user_id)
     words = configs.get('replace_words', {})
     text = "<b><u>🔀 ᴋᴇʏᴡᴏʀᴅ ᴍᴀᴘᴘᴇʀ</u></b>\n\nCaptions mein words change karne ke liye:\n"
     for old, new in words.items():
         text += f"• <code>{old}</code> ➜ <code>{new if new else '[DELETED]'}</code>\n"
     if not words: text += "<i>No replacements active.</i>"
     
     btn = [
         [InlineKeyboardButton('✚ Add Word', callback_data="settings#add_rep")],
         [InlineKeyboardButton('🗑️ Clear All', callback_data="settings#clear_rep")],
         back_btn
     ]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

  elif type == "add_rep":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>Format:</b> <code>OldWord : NewWord</code>\n\n(Example: <code>@OldChannel : @MyChannel</code>)")
     if ask.text and ":" in ask.text:
         old, new = [i.strip() for i in ask.text.split(":", 1)]
         configs = await get_configs(user_id)
         words = configs.get('replace_words', {})
         words[old] = new
         await update_configs(user_id, 'replace_words', words)
         await bot.send_message(user_id, f"✅ Mapping Saved: `{old}` -> `{new}`", reply_markup=InlineKeyboardMarkup([back_btn]))

  # --- [FEATURE] DONATE & VPS HOOK ---
  elif type == "donate":
     # Donation message with the VPS upgrade reason
     text = (
         "<b>💖 sᴜᴘᴘᴏʀᴛ & ᴅᴏɴᴀᴛᴇ</b>\n\n"
         "Agar aapko ye bot pasand hai aur aap <b>Thumbnail ke sath Unlimited Forwarding</b> chahte hain, "
         "toh consider karein donate karna.\n\n"
         "Aapka support humein bot ko bade <b>VPS Servers</b> par host karne mein madad karega! 🚀"
     )
     btn = [[InlineKeyboardButton("💬 Contact Admin", url="https://t.me/AK_ownerbot")], back_btn]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

  # --- BOTS & USERBOTS ---
  elif type == "bots":
     _bot = await db.get_bot(user_id)
     btn = [] 
     if _bot:
        btn.append([InlineKeyboardButton(f"🤖 {_bot['name']}", callback_data="settings#editbot")])
     else:
        btn.append([InlineKeyboardButton('✚ Add Bot Token', callback_data="settings#addbot")])
     btn.append([InlineKeyboardButton('📲 Add Userbot (Session)', callback_data="settings#adduserbot")])
     btn.append([InlineKeyboardButton('🔑 Add Userbot (Login)', callback_data="settings#addlogin")])
     btn.append(back_btn)
     await query.message.edit_text("<b>🤖 ᴍᴀɴᴀɢᴇ ᴡᴏʀᴋᴇʀs</b>", reply_markup=InlineKeyboardMarkup(btn))

  # --- FILTERS & PROTECT ---
  elif type == "filters":
     await query.message.edit_text("<b>🕵️ ꜰᴏʀᴡᴀʀᴅɪɴɢ ꜰɪʟᴛᴇʀs</b>", reply_markup=await filters_buttons(user_id))

  elif type == "nextfilters":
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

  # --- STATS ---
  elif type == "stats":
     users, bots = await db.total_users_bots_count()
     await query.message.edit_text(
        f"<b>📊 ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs</b>\n\n👤 Total Users: <code>{users}</code>\n🤖 Active Workers: <code>{bots}</code>\n🌐 Server: <code>Koyeb (VPS Ready)</code>",
        reply_markup=InlineKeyboardMarkup([back_btn]))

# ================= UI HELPERS ================= #

def main_buttons():
  buttons = [
    [InlineKeyboardButton('🤖 Workers', 'settings#bots'), InlineKeyboardButton('🖋️ Caption', 'settings#caption')],
    [InlineKeyboardButton('🖼️ Thumbnail', 'settings#thumbnail'), InlineKeyboardButton('🔀 Mapper', 'settings#replacements')],
    [InlineKeyboardButton('🕵️ Filters', 'settings#filters'), InlineKeyboardButton('📊 Stats', 'settings#stats')],
    [InlineKeyboardButton('💖 Support', 'settings#donate'), InlineKeyboardButton('🧪 Extra', 'settings#nextfilters')],
    [InlineKeyboardButton('• ᴄʟᴏsᴇ •', callback_data='help')]
  ]
  return InlineKeyboardMarkup(buttons)

async def filters_buttons(user_id):
  filter = await get_configs(user_id)
  f = filter['filters']
  def icon(v): return "✅" if v else "❌"
  buttons = [
    [InlineKeyboardButton('🏷️ Forward Tag', 'none'), InlineKeyboardButton(icon(filter["forward_tag"]), f'settings#updatefilter-forward_tag-{filter["forward_tag"]}')],
    [InlineKeyboardButton('🖍️ Text', 'none'), InlineKeyboardButton(icon(f["text"]), f'settings#updatefilter-text-{f["text"]}')],
    [InlineKeyboardButton('🎞️ Videos', 'none'), InlineKeyboardButton(icon(f["video"]), f'settings#updatefilter-video-{f["video"]}')],
    [InlineKeyboardButton('📷 Photos', 'none'), InlineKeyboardButton(icon(f["photo"]), f'settings#updatefilter-photo-{f["photo"]}')],
    [InlineKeyboardButton('• ʙᴀᴄᴋ', "settings#main")]
  ]
  return InlineKeyboardMarkup(buttons) 

async def next_filters_buttons(user_id):
  filter = await get_configs(user_id)
  def icon(v): return "✅" if v else "❌"
  buttons = [
    [InlineKeyboardButton('📊 Polls', 'none'), InlineKeyboardButton(icon(filter['filters']["poll"]), f'settings#updatefilter-poll-{filter["filters"]["poll"]}')],
    [InlineKeyboardButton('🔒 Protect Content', 'none'), InlineKeyboardButton(icon(filter["protect"]), f'settings#updatefilter-protect-{filter["protect"]}')],
    [InlineKeyboardButton('▶️ Duplicates', 'none'), InlineKeyboardButton(icon(filter["duplicate"]), f'settings#updatefilter-duplicate-{filter["duplicate"]}')],
    [InlineKeyboardButton('• ʙᴀᴄᴋ', "settings#main")]
  ]
  return InlineKeyboardMarkup(buttons)
