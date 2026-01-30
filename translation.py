import os
from config import Config

class Translation(object):
  # --- Introduction ---
  START_TXT = """<b>ʜɪ {}

ɪ'ᴍ ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴜᴛᴏ ꜰᴏʀᴡᴀʀᴅ ʙᴏᴛ (ᴠ𝟹)
ɪ ᴄᴀɴ ꜰᴏʀᴡᴀʀᴅ ᴍᴇssᴀɢᴇs ꜰʀᴏᴍ ᴀɴʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴀɴᴏᴛʜᴇʀ ᴡɪᴛʜ ᴘᴇʀsɪsᴛᴇɴᴛ ᴀᴜᴛᴏ-ʀᴇsᴜᴍᴇ ᴘᴏᴡᴇʀ.

ᴊᴏɪɴ ᴏᴜʀ ʙᴀᴄᴋᴜᴘ ᴄʜᴀɴɴᴇʟ ꜰᴏʀ ᴜᴘᴅᴀᴛᴇs ᴀɴᴅ sᴜᴘᴘᴏʀᴛ!</b>"""

  # --- Settings Guides ---
  CAPTION_HELP = """<b><u>📝 ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ɢᴜɪᴅᴇ</u></b>

Aap apni files par man-chaha caption laga sakte hain.
<b>Placeholders:</b>
• <code>{{filename}}</code> : File ka asli naam.
• <code>{{size}}</code> : File ka size (MB/GB).
• <code>{{caption}}</code> : File ka purana caption.

<i>Example: <code>{{filename}} uploaded by @MyBot</code></i>"""

  FILTER_HELP = """<b><u>🕵️ ꜰɪʟᴛᴇʀ sᴇᴛᴛɪɴɢs</u></b>

Chuno ki aapko source channel se kya-kya uthana hai:
✅ = Ye media forward hoga.
❌ = Ye media skip ho jayega.

<b>Tags:</b> Agar 'Forward Tag' ON hai, toh message 'Forwarded from...' ke saath jayega."""

  EXTRA_HELP = """<b><u>🧪 ᴇxᴛʀᴀ sᴇᴛᴛɪɴɢs (ᴘʀᴏ)</u></b>

• <b>ᴅᴜᴘʟɪᴄᴀᴛᴇ:</b> ON rakhne par bot pehle se bheji gayi file ko dubara nahi bhejega.
• <b>ᴘʀᴏᴛᴇᴄᴛ:</b> ON rakhne par content copy/forward nahi ho payega.
• <b>ᴋᴇʏᴡᴏʀᴅ:</b> Specific words ko replace ya delete karein."""

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
► <b>Keyword Mapper:</b> Change or remove specific words.
► <b>Admin Backup:</b> Sync files to your backup channel.
"""
  
  HOW_USE_TXT = """<b><u>⚠️ Setup Guide:</b></u>
1. Add a Bot or Userbot in /settings.
2. Set Target Channel (Bot must be admin).
3. Use /forward, provide source link, and start.

<b>Note:</b> Bot automatically poora channel scan karega!"""

  ABOUT_TXT = """<b>
╔════❰ ᴀᴅᴠᴀɴᴄᴇᴅ ꜰᴏʀᴡᴀʀᴅ ʙᴏᴛ ❱═❍⊱❁
║╭━━━━━━━━━━━━━━━➣
║┣⪼📃 ʙᴏᴛ : ғᴏʀᴡᴀʀᴅ ᴇʟɪᴛᴇ ᴠ𝟹
║┣⪼👦 ᴏᴡɴᴇʀ : @AK_ownerbot
║┣⪼🗣️ ʟᴀɴɢᴜᴀɢᴇ : ᴘʏᴛʜᴏɴ3
║┣⪼📚 ʟɪʙʀᴀʀʏ : ᴘʏʀᴏɢʀᴀᴍ
║╰━━━━━━━━━━━━━━━➣
╚══════════════════❍⊱❁</b>"""

  STATUS_TXT = """<b>
╔════❰ ʙᴏᴛ sᴛᴀᴛᴜs  ❱═❍⊱❁
║╭━━━━━━━━━━━━━━━➣
║┣⪼👱 ᴛᴏᴛᴀʟ ᴜsᴇʀs : <code>{}</code>
║┣⪼🤖 ᴛᴏᴛᴀʟ ʙᴏᴛs : <code>{}</code>
║┣⪼🔃 ᴀᴄᴛɪᴠᴇ ᴛᴀsᴋs : <code>{}</code>
║╰━━━━━━━━━━━━━━━➣
╚══════════════════❍⊱❁</b>""" 
  
  FROM_MSG = "<b>❪ sᴇᴛ sᴏᴜʀᴄᴇ ❫\n\nForward a message or send link from source chat.\n/cancel - To Cancel.</b>"
  TO_MSG = "<b>❪ ᴛᴀʀɢᴇᴛ ᴄʜᴀᴛ ❫\n\nChoose target from buttons or send ID.\n/cancel - To Cancel.</b>"
  SKIP_MSG = "<b><u>sᴋɪᴘ ᴍᴇssᴀɢᴇs 📃</u></b>\n\nKitne messages skip karne hain? Default = 0.\n/cancel - To Cancel."
  CANCEL = "<b>❌ Process Cancelled Successfully!</b>"

  # --- Problem #03 Fix: Main Status Template (MATCHED WITH REGIX.PY) ---
  TEXT = """<b>╔════❰ ꜰᴏʀᴡᴀʀᴅɪɴɢ sᴛᴀᴛᴜs ❱═❍⊱❁
║╭━━━━━━━━━━━━━━━➣
║┣⪼ ᴛᴏᴛᴀʟ: <code>{0}</code>
║┣⪼ ꜰᴇᴛᴄʜᴇᴅ: <code>{1}</code>
║┣⪼ ꜰᴏʀᴡᴀʀᴅᴇᴅ: <b>{2}</b>
║┃
║┣⪼ ᴅᴜᴘʟɪᴄᴀᴛᴇ: <code>{3}</code>
║┣⪼ ᴅᴇʟᴇᴛᴇᴅ: <code>{4}</code>
║┣⪼ sᴋɪᴘᴘᴇᴅ: <code>{5}</code>
║┣⪼ ꜰɪʟᴛᴇʀᴇᴅ: <code>{6}</code>
║┃
║┣⪼ sᴛᴀᴛᴜs: <code>{7}</code>
║┣⪼ ᴘʀᴏɢʀᴇss: <code>{8}%</code>
║╰━━━━━━━━━━━━━━━➣ 
╚════❰ {9} ❱══❍⊱❁</b>"""

  DUPLICATE_TEXT = """
╔════❰ ᴜɴᴇǫᴜɪғʏ sᴛᴀᴛᴜs ❱═❍⊱❁۪۪
║╭━━━━━━━━━━━━━━━➣
║┣⪼ ꜰᴇᴛᴄʜᴇᴅ: <code>{}</code>
║┣⪼ ᴅᴇʟᴇᴛᴇᴅ: <code>{}</code> 
║╰━━━━━━━━━━━━━━━➣
╚════❰ {} ❱══❍⊱❁۪۪
"""
  
  FORCE_MSG = "<b>⚠️ Access Denied!</b>\n\nAapne hamare mandatory channels join nahi kiye hain."

  PROGRESS = """
📊 <b><u>ᴘʀᴏɢʀᴇss ᴅᴇᴛᴀɪʟs</u></b>

📈 ᴘᴇʀᴄᴇɴᴛᴀɢᴇ : {0} %
⭕ ғᴇᴛᴄʜᴇᴅ : {1}
⚙️ ғᴏʀᴡᴀʀᴅᴇᴅ : {2}
🗞️ ʀᴇᴍᴀɴɪɴɢ : {3}
♻️ sᴛᴀᴛᴜs : {4}
⏳️ ᴇᴛᴀ : {5}
"""
