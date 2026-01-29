import os
from config import Config

class Translation(object):
  START_TXT = """<b>ʜɪ {}

ɪ'ᴍ ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴜᴛᴏ ꜰᴏʀᴡᴀʀᴅ ʙᴏᴛ (ᴠ𝟹)
ɪ ᴄᴀɴ ꜰᴏʀᴡᴀʀᴅ ᴍᴇssᴀɢᴇs ꜰʀᴏᴍ ᴀɴʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴀɴᴏᴛʜᴇʀ ᴡɪᴛʜ ᴘᴇʀsɪsᴛᴇɴᴛ ᴀᴜᴛᴏ-ʀᴇsᴜᴍᴇ ᴘᴏᴡᴇʀ.

ᴄʟɪᴄᴋ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴋɴᴏᴡ ᴍᴏʀᴇ ᴀʙᴏᴜᴛ ᴍʏ sᴜᴘᴇʀᴘᴏᴡᴇʀs!</b>"""

  HELP_TXT = """<b><u>🔆 ʜᴇʟᴘ ᴍᴇɴᴜ</b></u>

<b>📚 Commands:</b>
⏣ /start - Check if I'm alive
⏣ /forward - Start forwarding messages
⏣ /unequify - Remove duplicates in channels
⏣ /settings - Configure Keyword Mapping, Thumb, & Backup
⏣ /reset - Reset all configurations
⏣ /stop - Cancel ongoing task

<b>💢 Pro Features:</b>
► <b>Auto-Resume:</b> Task resumes automatically after bot restart.
► <b>Keyword Mapper:</b> Change or remove specific words from captions.
► <b>Admin Backup:</b> Automatically copy all files to your backup channel.
► <b>Dynamic Bar:</b> Modern solid-block progress tracking.
► <b>Restricted Support:</b> Forward even from restricted chats.
"""
  
  HOW_USE_TXT = """<b><u>⚠️ Setup Guide:</b></u>
1. Add a Bot (via Token) or Userbot (via Login/Session) in /settings.
2. Set your Target Channel in /settings (Bot/Userbot must be admin).
3. (Optional) Set Keyword Mapping & Backup Channel in /settings.
4. Use /forward, provide source link, and start.

<b><u>🚫 Anti-Ban Warning:</b></u>
Telegram filters are strict. Use accounts older than 3 months and set Two-Step Verification (2FA) before logging in here to avoid account deletion.</b>"""

  ABOUT_TXT = """<b>
╔════❰ ᴀᴅᴠᴀɴᴄᴇᴅ ꜰᴏʀᴡᴀʀᴅ ʙᴏᴛ ❱═❍⊱❁
║╭━━━━━━━━━━━━━━━➣
║┣⪼📃 ʙᴏᴛ : ғᴏʀᴡᴀʀᴅ ᴇʟɪᴛᴇ ᴠ𝟹
║┣⪼👦 ᴏᴡɴᴇʀ : ᴀᴅᴍɪɴ
║┣⪼🗣️ ʟᴀɴɢᴜᴀɢᴇ : ᴘʏᴛʜᴏɴ3
║┣⪼📚 ʟɪʙʀᴀʀʏ : ᴘʏʀᴏɢʀᴀᴍ
║┣⪼🗒️ ᴠᴇʀsɪᴏɴ : 3.0.0 (sᴛᴀʙʟᴇ)
║╰━━━━━━━━━━━━━━━➣
╚══════════════════❍⊱❁</b>"""

  STATUS_TXT = """<b>
╔════❰ ʙᴏᴛ sᴛᴀᴛᴜs  ❱═❍⊱❁
║╭━━━━━━━━━━━━━━━➣
║┣⪼👱 ᴛᴏᴛᴀʟ ᴜsᴇʀs : <code>{}</code>
║┃
║┣⪼🤖 ᴛᴏᴛᴀʟ ʙᴏᴛs : <code>{}</code>
║┃
║┣⪼🔃 ᴀᴄᴛɪᴠᴇ ᴛᴀsᴋs : <code>{}</code>
║╰━━━━━━━━━━━━━━━➣
╚══════════════════❍⊱❁</b>""" 
  
  FROM_MSG = "<b>❪ SET SOURCE ❫\n\nForward a message or send link from source chat.\n/cancel - To Cancel.</b>"

  TO_MSG = "<b>❪ TARGET CHAT ❫\n\nChoose target from buttons.\n/cancel - To Cancel.</b>"

  SKIP_MSG = "<b><u>sᴋɪᴘ ᴍᴇssᴀɢᴇs 📃</u></b>\n\nDefault = 0. Example: Enter 10 to skip first 10 messages.\n/cancel - To Cancel."

  CANCEL = "<b>❌ Process Cancelled Successfully!</b>"

  BOT_DETAILS = "<b><u>📄 BOT DETAILS</b></u>\n\n<b>➣ NAME:</b> <code>{}</code>\n<b>➣ ID:</b> <code>{}</code>\n<b>➣ USER:</b> @{}"

  USER_DETAILS = "<b><u>📄 USERBOT DETAILS</b></u>\n\n<b>➣ NAME:</b> <code>{}</code>\n<b>➣ ID:</b> <code>{}</code>\n<b>➣ USER:</b> @{}"  
         
  # Upgraded Text for Progress with Dynamic Bar Support
  TEXT = """<b>╔════❰ ꜰᴏʀᴡᴀʀᴅɪɴɢ sᴛᴀᴛᴜs ❱═❍⊱❁
║╭━━━━━━━━━━━━━━━➣
║┣⪼ ᴛᴏᴛᴀʟ: <code>{}</code>
║┣⪼ ꜰᴇᴛᴄʜᴇᴅ: <code>{}</code>
║┣⪼ ꜰᴏʀᴡᴀʀᴅᴇᴅ: <b>{}</b>
║┃
║┣⪼ ᴅᴜᴘʟɪᴄᴀᴛᴇ: <code>{}</code>
║┣⪼ ᴅᴇʟᴇᴛᴇᴅ: <code>{}</code>
║┣⪼ sᴋɪᴘᴘᴇᴅ: <code>{}</code>
║┣⪼ ꜰɪʟᴛᴇʀᴇᴅ: <code>{}</code>
║┃
║┣⪼ sᴛᴀᴛᴜs: <code>{}</code>
║┣⪼ ᴘʀᴏɢʀᴇss: <code>{}%</code>
║╰━━━━━━━━━━━━━━━➣ 
╚════❰ {} ❱══❍⊱❁</b>"""

  DUPLICATE_TEXT = """
╔════❰ ᴜɴᴇǫᴜɪғʏ sᴛᴀᴛᴜs ❱═❍⊱❁۪۪
║╭━━━━━━━━━━━━━━━➣
║┣⪼ ꜰᴇᴛᴄʜᴇᴅ: <code>{}</code>
║┣⪼ ᴅᴇʟᴇᴛᴇᴅ: <code>{}</code> 
║╰━━━━━━━━━━━━━━━➣
╚════❰ {} ❱══❍⊱❁۪۪
"""
  
  PROGRESS = """
📊 <b><u>ᴘʀᴏɢʀᴇss ᴅᴇᴛᴀɪʟs</u></b>

📈 ᴘᴇʀᴄᴇɴᴛᴀɢᴇ : {0} %
⭕ ғᴇᴛᴄʜᴇᴅ : {1}
⚙️ ғᴏʀᴡᴀʀᴅᴇᴅ : {2}
🗞️ ʀᴇᴍᴀɴɪɴɢ : {3}
♻️ sᴛᴀᴛᴜs : {4}
⏳️ ᴇᴛᴀ : {5}
"""
