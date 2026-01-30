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

  # --- [FEATURE] SAVED TARGETS (Multi-ID Fix) ---
  elif type == "manage_targets":
     configs = await get_configs(user_id)
     targets = configs.get('targets', 'Not Set')
     text = (
         "<b>🎯 sᴀᴠᴇᴅ ᴛᴀʀɢᴇᴛs</b>\n\n"
         f"Current IDs: <code>{targets}</code>\n\n"
         "In IDs ko set karne ke baad aapko <code>/forward</code> setup ke waqt baar-baar IDs type nahi karni padengi."
     )
     btn = [[InlineKeyboardButton('🖋️ Edit Saved Targets', callback_data="settings#set_targets")], back_btn]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

  elif type == "set_targets":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>IDs Bhejein:</b>\n\nJin channels mein forward karna hai unki IDs comma (,) se alag karke bhejein.\n\nExample: <code>-100123, -100456, -100789</code>")
     if ask.text and not ask.text.startswith('/'):
         clean_ids = ask.text.replace(" ", "")
         await update_configs(user_id, 'targets', clean_ids)
         await bot.send_message(user_id, "✅ **Targets Saved!**\nAb setup ke waqt 'Use Saved Targets' ka button dikhega.", reply_markup=InlineKeyboardMarkup([back_btn]))
     else:
         await bot.send_message(user_id, "❌ **Cancelled!**", reply_markup=InlineKeyboardMarkup([back_btn]))

  # --- [FIX] CAPTION EDITING ---
  elif type == "caption":
     configs = await get_configs(user_id)
     cap = configs.get('caption', 'Default')
     text = f"<b>🖋️ ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ</b>\n\n<b>Current:</b>\n<code>{cap}</code>"
     btn = [[InlineKeyboardButton('🖋️ Edit Caption', callback_data="settings#addcaption")], back_btn]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

  elif type == "addcaption":
     await query.message.delete()
     prompt = (
         "<b>Bhai, apni Custom Caption bhejein:</b>\n\n"
         "Variables jo aap use kar sakte hain:\n"
         "• <code>{filename}</code> - File ka naam\n"
         "• <code>{size}</code> - File ka size\n"
         "• <code>{caption}</code> - Original caption"
     )
     ask = await bot.ask(user_id, prompt)
     if ask.text and not ask.text.startswith('/'):
         await update_configs(user_id, 'caption', ask.text)
         await bot.send_message(user_id, "✅ **Caption Updated Successfully!**", reply_markup=InlineKeyboardMarkup([back_btn]))

  # --- THUMBNAIL MENU ---
  elif type == "thumbnail":
     configs = await get_configs(user_id)
     thumb = configs.get('thumbnail')
     text = Translation.THUMBNAIL_HELP.format(limit=Config.THUMB_LIMIT)
     btn = [[InlineKeyboardButton('🖼️ Set Thumbnail', callback_data="settings#set_thumb")]]
     if thumb:
         btn.append([InlineKeyboardButton('🗑️ Delete Thumbnail', callback_data="settings#del_thumb")])
     btn.append(back_btn)
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

  elif type == "set_thumb":
     await query.message.delete()
     ask = await bot.ask(user_id, "<b>Bhai, thumbnail ki photo bhejein:</b>")
     if ask.photo:
         await update_configs(user_id, 'thumbnail', ask.photo.file_id)
         await bot.send_message(user_id, "✅ **Thumbnail Set!**", reply_markup=InlineKeyboardMarkup([back_btn]))

  elif type == "del_thumb":
     await update_configs(user_id, 'thumbnail', None)
     await query.answer("Thumbnail Deleted! 🗑️", show_alert=True)
     await query.message.edit_text("✅ Thumbnail removed.", reply_markup=InlineKeyboardMarkup([back_btn]))

  # --- BOTS & WORKERS ---
  elif type == "bots":
     _bot = await db.get_bot(user_id)
     btn = [] 
     if _bot:
        btn.append([InlineKeyboardButton(f"🤖 {_bot['name']}", callback_data="settings#editbot")])
     else:
        btn.append([InlineKeyboardButton('✚ Add Bot Token', callback_data="settings#addbot")])
     btn.append([InlineKeyboardButton('📲 Add Userbot (Session)', callback_data="settings#adduserbot")])
     btn.append(back_btn)
     await query.message.edit_text("<b>🤖 ᴍᴀɴᴀɢᴇ ᴡᴏʀᴋᴇʀs</b>", reply_markup=InlineKeyboardMarkup(btn))

  # --- FILTERS & STATS & DONATE ---
  elif type == "filters":
     await query.message.edit_text("<b>🕵️ ꜰᴏʀᴡᴀʀᴅɪɴɢ ꜰɪʟᴛᴇʀs</b>", reply_markup=await filters_buttons(user_id))

  elif type == "stats":
     users, bots = await db.total_users_bots_count()
     await query.message.edit_text(
        f"<b>📊 ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs</b>\n\n👤 Users: <code>{users}</code>\n🤖 Workers: <code>{bots}</code>\n🌐 Server: <code>Elite V3 Ready</code>",
        reply_markup=InlineKeyboardMarkup([back_btn]))

  elif type == "donate":
     await query.message.edit_text(Translation.DONATE_TXT, reply_markup=InlineKeyboardMarkup([back_btn]))

# ================= UI HELPERS ================= #

def main_buttons():
  buttons = [
    [InlineKeyboardButton('🤖 Workers', 'settings#bots'), InlineKeyboardButton('🖋️ Caption', 'settings#caption')],
    [InlineKeyboardButton('🖼️ Thumbnail', 'settings#thumbnail'), InlineKeyboardButton('🎯 Saved Targets', 'settings#manage_targets')],
    [InlineKeyboardButton('🔀 Mapper', 'settings#replacements'), InlineKeyboardButton('🕵️ Filters', 'settings#filters')],
    [InlineKeyboardButton('📊 Stats', 'settings#stats'), InlineKeyboardButton('💖 Support', 'settings#donate')],
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
