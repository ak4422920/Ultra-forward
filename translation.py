import os
from config import Config

class Translation(object):
  # --- UI & Branding ---
  START_TXT = """<b>ʜɪ {} 👋

ɪ'ᴍ ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴜᴛᴏ ꜰᴏʀᴡᴀʀᴅ ʙᴏᴛ (ᴠ𝟹)
ɪ ᴄᴀɴ ꜰᴏʀᴡᴀʀᴅ ᴍᴇssᴀɢᴇs ꜰʀᴏᴍ ᴀɴʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴀɴᴏᴛʜᴇʀ.

ᴊᴏɪɴ ᴏᴜʀ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟs ꜰᴏʀ sᴜᴘᴘᴏʀᴛ!</b>"""

  # --- [NEW] Multiple Force Subscribe Message ---
  FORCE_MSG = """<b>❌ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ!

Aapne hamare zaroori channels join nahi kiye hain. Bot use karne ke liye niche diye gaye sabhi channels join karein:</b>"""

  # --- Settings Guides (Silicon ID Removed) ---
  CAPTION_HELP = """<b><u>📝 ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ɢᴜɪᴅᴇ</u></b>

Aap apni files par man-chaha caption laga sakte hain.
<b>Placeholders:</b>
• <code>{filename}</code> : File ka asli naam.
• <code>{size}</code> : File ka size (MB/GB).
• <code>{caption}</code> : File ka purana caption.

<i>Example: <code>{filename} - Shared by @MyBot</code></i>"""

  FILTER_HELP = """<b><u>🕵️ ꜰɪʟᴛᴇʀ sᴇᴛᴛɪɴɢs</u></b>

Chuno ki aapko source channel se kya-kya uthana hai:
✅ = Ye media forward hoga.
❌ = Ye media skip ho jayega.

<b>Note:</b> Agar 'Forward Tag' ON hai, toh message 'Forwarded from...' ke saath jayega."""

  # --- [UPDATED] Thumbnail Warning & Donation Hook ---
  THUMBNAIL_HELP = """<b><u>🖼️ ᴄᴜsᴛᴏᴍ ᴛʜᴜᴍʙɴᴀɪʟ ɢᴜɪᴅᴇ</u></b>

Aap apni files par custom thumbnail laga sakte hain.

⚠️ <b><u>ᴢᴀʀᴏᴏʀɪ sᴏᴏᴄʜɴᴀ:</u></b>
Thumbnail lagane par bot ko files download aur re-upload karni padti hain.
• Isliye abhi ke liye maximum <b>{limit} files</b> hi forward hongi.
• Forwarding ki speed thodi kam ho jayegi.

💡 <b><u>ᴢᴀʏᴀᴅᴀ ʟɪᴍɪᴛ ᴄʜᴀʜɪʏᴇ?</u></b>
Agar aap chahte hain ki thumbnail ke saath bhi unlimited forwarding ho, toh <b>Admin ko support/donate karein</b> taaki hum bot ko bade VPS server par host kar sakein! ❤️"""

  EXTRA_HELP = """<b><u>🧪 ᴇxᴛʀᴀ sᴇᴛᴛɪɴɢs (ᴘʀᴏ)</u></b>

• <b>ᴅᴜᴘʟɪᴄᴀᴛᴇ:</b> ON rakhne par bot dubara wahi file nahi bhejega.
• <b>ᴘʀᴏᴛᴇᴄᴛ:</b> Content copy/forward restricted rahega.
• <b>ᴋᴇʏᴡᴏʀᴅ:</b> Captions se links ya words badalne ke liye.
• <b>ᴀᴜᴛᴏ-ʙᴀᴄᴋᴜᴘ:</b> Aapki har file background mein safe rahegi."""

  HELP_TXT = """<b><u>🔆 ʜᴇʟᴘ ᴍᴇɴᴜ</u></b>

<b>📚 Commands:</b>
⏣ /start - Bot status check karein
⏣ /forward - Forwarding shuru karein (1 Source -> 5 Targets)
⏣ /unequify - Channel se duplicates saaf karein
⏣ /settings - Caption, Thumb, aur Mapper set karein
⏣ /stop - Ongoing task ko cancel karein

<b>💢 Elite Features:</b>
► <b>Auto-Resume:</b> Server restart ke baad task wahi se shuru hoga.
► <b>Keyword Mapper:</b> Captions se links replace karein.
► <b>Multi-Target:</b> Ek sath 5 channels mein post karein.
► <b>No-Limit:</b> Bot poora channel automatically scan karega!"""

  # --- Stats & Messages ---
  ABOUT_TXT = """<b>
╔════❰ ᴀᴅᴠᴀɴᴄᴇᴅ ꜰᴏʀᴡᴀʀᴅ ᴇʟɪᴛᴇ ❱═❍⊱❁
║╭━━━━━━━━━━━━━━━➣
║┣⪼📃 ʙᴏᴛ : ғᴏʀᴡᴀʀᴅ ᴇʟɪᴛᴇ ᴠ𝟹
║┣⪼👦 ᴏᴡɴᴇʀ : @AK_ownerbot
║┣⪼🗣️ ʟᴀɴɢᴜᴀɢᴇ : ᴘʏᴛʜᴏɴ3
║┣⪼🌐 ʜᴏsᴛ : KOYEB (VPS Ready)
║╰━━━━━━━━━━━━━━━➣
╚══════════════════❍⊱❁</b>"""

  STATUS_TXT = """<b>
╔════❰ ʙᴏᴛ sᴛᴀᴛᴜs ❱═❍⊱❁
║╭━━━━━━━━━━━━━━━➣
║┣⪼👱 ᴛᴏᴛᴀʟ ᴜsᴇʀs : <code>{}</code>
║┣⪼🤖 ᴛᴏᴛᴀʟ ʙᴏᴛs : <code>{}</code>
║┣⪼🔃 ᴀᴄᴛɪᴠᴇ ᴛᴀsᴋs : <code>{}</code>
║╰━━━━━━━━━━━━━━━➣
╚══════════════════❍⊱❁</b>""" 
  
  FROM_MSG = "<b>❪ sᴇᴛ sᴏᴜʀᴄᴇ ❫\n\nSource channel ka link bhejein ya koi bhi message forward karein.\n/cancel - To Cancel.</b>"
  TO_MSG = "<b>❪ ᴛᴀʀɢᴇᴛ ᴄʜᴀᴛs ❫\n\nTarget channels ki IDs bhejein (Max 5 targets supported).\nExample: <code>-100123, -100456</code>\n/cancel - To Cancel.</b>"
  SKIP_MSG = "<b><u>sᴋɪᴘ ᴍᴇssᴀɢᴇs 📃</u></b>\n\nKitne purane messages skip karne hain? Default = 0.\n/cancel - To Cancel."
  CANCEL = "<b>❌ Process Cancelled Successfully!</b>"

  # --- Status Template ---
  TEXT = """<b>╔════❰ ꜰᴏʀᴡᴀʀᴅɪɴɢ sᴛᴀᴛᴜs ❱═❍⊱❁
║╭━━━━━━━━━━━━━━━➣
║┣⪼ ᴛᴏᴛᴀʟ: <code>{0}</code>
║┣⪼ ꜰᴇᴛᴄʜᴇᴅ: <code>{1}</code>
║┣⪼ ꜰᴏʀᴡᴀʀᴅᴇᴅ: <b>{2}</b>
║┃
║┣⪼ ᴅᴜᴘʟɪᴄᴀᴛᴇ: <code>{3}</code>
║┣⪼ sᴋɪᴘᴘᴇᴅ: <code>{5}</code>
║┣⪼ sᴛᴀᴛᴜs: <code>{7}</code>
║┣⪼ ᴘʀᴏɢʀᴇss: <code>{8}%</code>
║╰━━━━━━━━━━━━━━━➣ 
╚════❰ {9} ❱══❍⊱❁</b>"""

  PROGRESS = """
📊 <b><u>ᴘʀᴏɢʀᴇss ᴅᴇᴛᴀɪʟs</u></b>

📈 ᴘᴇʀᴄᴇɴᴛᴀɢᴇ : {0} %
⭕ ғᴇᴛᴄʜᴇᴅ : {1}
⚙️ ғᴏʀᴡᴀʀᴅᴇᴅ : {2}
⏳️ ᴇᴛᴀ : {5}
"""
