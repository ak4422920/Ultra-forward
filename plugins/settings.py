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

  # --- SAVED TARGETS ---
  elif type == "manage_targets":
     configs = await get_configs(user_id)
     targets = configs.get('targets', 'Not Set')
     text = f"<b>🎯 sᴀᴠᴇᴅ ᴛᴀʀɢᴇᴛs</b>\n\nIDs: <code>{targets}</code>"
     btn = [[InlineKeyboardButton('🖋️ Edit Saved Targets', callback_data="settings#set_targets")], back_btn]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

  elif type == "set_targets":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>IDs Bhejein:</b> (Comma se alag karein)\nExample: <code>-1001, -1002</code>")
     if ask.text and not ask.text.startswith('/'):
         await update_configs(user_id, 'targets', ask.text.replace(" ", ""))
         await bot.send_message(user_id, "✅ **Targets Saved!**", reply_markup=InlineKeyboardMarkup([back_btn]))

  # --- CAPTION EDITING ---
  elif type == "caption":
     configs = await get_configs(user_id)
     cap = configs.get('caption', 'Default')
     text = f"<b>🖋️ ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ</b>\n\n<code>{cap}</code>"
     btn = [[InlineKeyboardButton('🖋️ Edit Caption', callback_data="settings#addcaption")], back_btn]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

  elif type == "addcaption":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>Bhai, caption bhejein:</b>\nVars: `{filename}`, `{size}`, `{caption}`")
     if ask.text and not ask.text.startswith('/'):
         await update_configs(user_id, 'caption', ask.text)
         await bot.send_message(user_id, "✅ **Caption Updated!**", reply_markup=InlineKeyboardMarkup([back_btn]))

  # --- KEYWORD MAPPER (Added Now) ---
  elif type == "replacements":
     configs = await get_configs(user_id)
     words = configs.get('replace_words', {})
     text = "<b><u>🔀 ᴋᴇʏᴡᴏʀᴅ ᴍᴀᴘᴘᴇʀ</u></b>\n\n"
     for old, new in words.items():
         text += f"• <code>{old}</code> ➜ <code>{new}</code>\n"
     if not words: text += "<i>No replacements active.</i>"
     btn = [
         [InlineKeyboardButton('✚ Add Mapping', callback_data="settings#add_rep")],
         [InlineKeyboardButton('🗑️ Clear All', callback_data="settings#clear_rep")],
         back_btn
     ]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

  elif type == "add_rep":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>Format:</b> `OldWord : NewWord`")
     if ask.text and ":" in ask.text:
         old, new = [i.strip() for i in ask.text.split(":", 1)]
         configs = await get_configs(user_id)
         words = configs.get('replace_words', {})
         words[old] = new
         await update_configs(user_id, 'replace_words', words)
         await bot.send_message(user_id, f"✅ Mapping: `{old}` -> `{new}`", reply_markup=InlineKeyboardMarkup([back_btn]))

  elif type == "clear_rep":
     await update_configs(user_id, 'replace_words', {})
     await query.answer("Mappings Cleared! 🗑️")
     await query.message.edit_text("✅ All replacements cleared.", reply_markup=InlineKeyboardMarkup([back_btn]))

  # --- THUMBNAIL ---
  elif type == "thumbnail":
     configs = await get_configs(user_id)
     thumb = configs.get('thumbnail')
     btn = [[InlineKeyboardButton('🖼️ Set Thumbnail', callback_data="settings#set_thumb")]]
     if thumb: btn.append([InlineKeyboardButton('🗑️ Delete', callback_data="settings#del_thumb")])
     btn.append(back_btn)
     await query.message.edit_text("<b>🖼️ ᴛʜᴜᴍʙɴᴀɪʟ sᴇᴛᴛɪɴɢs</b>", reply_markup=InlineKeyboardMarkup(btn))

  elif type == "set_thumb":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>Thumbnail photo bhejein:</b>")
     if ask.photo:
         await update_configs(user_id, 'thumbnail', ask.photo.file_id)
         await bot.send_message(user_id, "✅ **Thumbnail Saved!**", reply_markup=InlineKeyboardMarkup([back_btn]))

  # --- FILTERS & EXTRA ---
  elif type == "filters":
     await query.message.edit_text("<b>🕵️ ꜰᴏʀᴡᴀʀᴅɪɴɢ ꜰɪʟᴛᴇʀs</b>", reply_markup=await filters_buttons(user_id))

  elif type == "nextfilters":
     await query.message.edit_text("<b>🧪 ᴇxᴛʀᴀ sᴇᴛᴛɪɴɢs</b>", reply_markup=await next_filters_buttons(user_id))

  elif "updatefilter" in type:
     # settings#updatefilter-key-val
     _, key, val = type.split('-')
     new_val = False if val == "True" else True
     configs = await get_configs(user_id)
     if key in ["forward_tag", "duplicate", "protect"]:
         await update_configs(user_id, key, new_val)
     else:
         f = configs.get('filters', {})
         f[key] = new_val
         await update_configs(user_id, 'filters', f)
     
     # Toggle switch ke baad wahi page reload hoga
     markup = await next_filters_buttons(user_id) if key in ['poll', 'protect', 'duplicate'] else await filters_buttons(user_id)
     await query.edit_message_reply_markup(reply_markup=markup)

  # --- WORKERS & STATS ---
  elif type == "bots":
     _bot = await db.get_bot(user_id)
     btn = [[InlineKeyboardButton(f"🤖 {_bot['name']}" if _bot else '✚ Add Bot', callback_data="settings#addbot")]]
     btn.append([InlineKeyboardButton('📲 Add Userbot', callback_data="settings#adduserbot")])
     btn.append(back_btn)
     await query.message.edit_text("<b>🤖 ᴍᴀɴᴀɢᴇ ᴡᴏʀᴋᴇʀs</b>", reply_markup=InlineKeyboardMarkup(btn))

  elif type == "stats":
     users, bots = await db.total_users_bots_count()
     await query.message.edit_text(f"<b>📊 sᴛᴀᴛs:</b>\nUsers: {users}\nWorkers: {bots}", reply_markup=InlineKeyboardMarkup([back_btn]))

  elif type == "donate":
     await query.message.edit_text("<b>💖 Support: @AK_ownerbot</b>", reply_markup=InlineKeyboardMarkup([back_btn]))

# ================= UI HELPERS ================= #

def main_buttons():
  return InlineKeyboardMarkup([
    [InlineKeyboardButton('🤖 Workers', 'settings#bots'), InlineKeyboardButton('🖋️ Caption', 'settings#caption')],
    [InlineKeyboardButton('🖼️ Thumbnail', 'settings#thumbnail'), InlineKeyboardButton('🎯 Targets', 'settings#manage_targets')],
    [InlineKeyboardButton('🔀 Mapper', 'settings#replacements'), InlineKeyboardButton('🕵️ Filters', 'settings#filters')],
    [InlineKeyboardButton('📊 Stats', 'settings#stats'), InlineKeyboardButton('💖 Support', 'settings#donate')],
    [InlineKeyboardButton('🧪 Extra', 'settings#nextfilters'), InlineKeyboardButton('• ᴄʟᴏsᴇ •', callback_data='help')]
  ])

async def filters_buttons(user_id):
  cfg = await get_configs(user_id)
  f = cfg.get('filters', {})
  def icon(v): return "✅" if v else "❌"
  return InlineKeyboardMarkup([
    [InlineKeyboardButton('🏷️ Tag', 'none'), InlineKeyboardButton(icon(cfg.get("forward_tag")), f'settings#updatefilter-forward_tag-{cfg.get("forward_tag")}')],
    [InlineKeyboardButton('📝 Text', 'none'), InlineKeyboardButton(icon(f.get("text")), f'settings#updatefilter-text-{f.get("text")}')],
    [InlineKeyboardButton('🎞️ Video', 'none'), InlineKeyboardButton(icon(f.get("video")), f'settings#updatefilter-video-{f.get("video")}')],
    [InlineKeyboardButton('🖼️ Photo', 'none'), InlineKeyboardButton(icon(f.get("photo")), f'settings#updatefilter-photo-{f.get("photo")}')],
    [InlineKeyboardButton('• ʙᴀᴄᴋ', "settings#main")]
  ])

async def next_filters_buttons(user_id):
  cfg = await get_configs(user_id)
  f = cfg.get('filters', {})
  def icon(v): return "✅" if v else "❌"
  return InlineKeyboardMarkup([
    [InlineKeyboardButton('📊 Polls', 'none'), InlineKeyboardButton(icon(f.get("poll")), f'settings#updatefilter-poll-{f.get("poll")}')],
    [InlineKeyboardButton('🔒 Protect', 'none'), InlineKeyboardButton(icon(cfg.get("protect")), f'settings#updatefilter-protect-{cfg.get("protect")}')],
    [InlineKeyboardButton('▶️ Duplicates', 'none'), InlineKeyboardButton(icon(cfg.get("duplicate")), f'settings#updatefilter-duplicate-{cfg.get("duplicate")}')],
    [InlineKeyboardButton('• ʙᴀᴄᴋ', "settings#main")]
  ])
