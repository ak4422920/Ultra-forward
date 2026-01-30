import os
import sys
import asyncio 
import datetime
import psutil
from pyrogram.types import Message
from database import db, mongodb_version
from config import Config, temp
from platform import python_version
from translation import Translation
from pyrogram import Client, filters, enums, __version__ as pyrogram_version
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaDocument

# Professional Main Buttons (Elite V3 Branding)
main_buttons = [
    [InlineKeyboardButton('📖 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs', callback_data='help')],
    [InlineKeyboardButton('📢 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url=f"{Config.FORCE_SUB_CHANNEL}")],
    [InlineKeyboardButton('💳 sᴜᴘᴘᴏʀᴛ & ᴅᴏɴᴀᴛᴇ', callback_data='donate')]
]

# =================== START FUNCTION (WITH MULTI-FORCE SUB) =================== #

@Client.on_message(filters.private & filters.command(['start']))
async def start(client, message):
    user = message.from_user
    
    # --- [FEATURE] MULTIPLE FORCE SUBSCRIBE LOGIC ---
    if Config.FORCE_SUB_ON:
        not_joined = []
        for channel_id in Config.FORCE_SUB_CHANNELS:
            try:
                member = await client.get_chat_member(channel_id, user.id)
                if member.status == enums.ChatMemberStatus.BANNED:
                    return await message.reply_text("<b>❌ Error:</b> Aapko bot se ban kiya gaya hai.")
            except Exception:
                # Agar join nahi kiya hai toh list mein add karein
                not_joined.append(channel_id)

        if not_joined:
            buttons = []
            for i, ch_id in enumerate(not_joined, 1):
                try:
                    chat = await client.get_chat(ch_id)
                    buttons.append([InlineKeyboardButton(f"ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ {i} 📡", url=f"https://t.me/{chat.username}" if chat.username else Config.FORCE_SUB_CHANNEL)])
                except:
                    continue
            
            buttons.append([InlineKeyboardButton("↻ ᴛʀʏ ᴀɢᴀɪɴ", url=f"https://t.me/{client.username}?start=start")])
            return await message.reply_text(
                text=Translation.FORCE_MSG if hasattr(Translation, 'FORCE_MSG') else "<b>ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ.</b>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    # User registration in Database
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
        await client.send_message(
            chat_id=Config.LOG_CHANNEL,
            text=f"<b>#NewUser</b>\n\n<b>ID:</b> <code>{user.id}</code>\n<b>Name:</b> {user.mention}\n<b>Date:</b> {datetime.datetime.now().strftime('%Y-%m-%d')}"
        )
    
    await message.reply_text(
        text=Translation.START_TXT.format(user.first_name),
        reply_markup=InlineKeyboardMarkup(main_buttons)
    )

# ================== RESTART (ADMIN ONLY) ================== #

@Client.on_message(filters.private & filters.command(['restart']) & filters.user(Config.BOT_OWNER_ID))
async def restart(client, message):
    msg = await message.reply_text("<b>⚙️ sᴇʀᴠᴇʀ sᴛᴀᴛᴜs:</b> <i>Restarting...</i>")
    await asyncio.sleep(2)
    await msg.edit("<b>✅ sᴇʀᴠᴇʀ ʀᴇsᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b>\nAuto-Resume engine active ho raha hai...")
    os.execl(sys.executable, sys.executable, *sys.argv)

# ================== CALLBACK ACTIONS ================== #

@Client.on_callback_query(filters.regex(r'^help'))
async def helpcb(bot, query):
    await query.message.edit_text(
        text=Translation.HELP_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('❓ ʜᴏᴡ ᴛᴏ ᴜsᴇ', callback_data='how_to_use')],
            [InlineKeyboardButton('⚙️ sᴇᴛᴛɪɴɢs', callback_data='settings#main'), InlineKeyboardButton('📊 sᴛᴀᴛᴜs', callback_data='status')],
            [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='back'), InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about')]
        ])
    )

@Client.on_callback_query(filters.regex(r'^back'))
async def back(bot, query):
    await query.message.edit_text(
       text=Translation.START_TXT.format(query.from_user.first_name),
       reply_markup=InlineKeyboardMarkup(main_buttons)
    )

@Client.on_callback_query(filters.regex(r'^how_to_use'))
async def how_to_use(bot, query):
    await query.message.edit_text(
        text=Translation.HOW_USE_TXT,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='help')]]),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r'^about'))
async def about(bot, query):
    await query.message.edit_text(
        text=Translation.ABOUT_TXT,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='back')]]),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r'^status'))
async def status(bot, query):
    users_count, bots_count = await db.total_users_bots_count()
    # Active tasks count from temp global
    active_tasks = len(temp.lock)
    
    await query.message.edit_text(
        text=Translation.STATUS_TXT.format(users_count, bots_count, active_tasks),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='help'), InlineKeyboardButton('🖥️ sᴇʀᴠᴇʀ sᴛᴀᴛs', callback_data='server_status')]
        ])
    )

@Client.on_callback_query(filters.regex(r'^server_status'))
async def server_status(bot, query):
    ram = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent()
    
    # Uptime Logic
    uptime = str(datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())).split('.')[0]
    
    text = (
        "<b>🖥️ sᴇʀᴠᴇʀ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ</b>\n\n"
        f"<b>• CPU Usage:</b> <code>{cpu}%</code>\n"
        f"<b>• RAM Usage:</b> <code>{ram}%</code>\n"
        f"<b>• Uptime:</b> <code>{uptime}</code>\n"
        f"<b>• Status:</b> <code>VPS Ready 🚀</code>"
    )
    
    await query.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='status')]])
    )

@Client.on_callback_query(filters.regex(r'^donate'))
async def donate_cb(bot, query):
    # Donation hook logic as discussed
    text = (
        "<b>💳 sᴜᴘᴘᴏʀᴛ & ᴅᴏɴᴀᴛᴇ</b>\n\n"
        "Aapka support humein bot ko bade <b>VPS Servers</b> par host karne mein madad karta hai.\n\n"
        "🌟 <b>Donators ke liye special benefits:</b>\n"
        "• Thumbnail ke sath Unlimited Forwarding.\n"
        "• Faster processing speed.\n\n"
        "Contact Admin: @AK_ownerbot"
    )
    await query.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='back')]])
    )

# =================== DONATE COMMAND =================== #

@Client.on_message(filters.private & filters.command(['donate']))
async def donate_cmd(client, message):
    await message.reply_text("<b>💖 Support Admin:</b> @AK_ownerbot\nDonate karke humein bot ko better banane mein madad karein!")
