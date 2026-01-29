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

# Professional Main Buttons
main_buttons = [
    [InlineKeyboardButton('❗️ ʜᴇʟᴘ', callback_data='help')],
    [InlineKeyboardButton('📢 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url=f"{Config.FORCE_SUB_CHANNEL}")],
    [InlineKeyboardButton('💳 ᴅᴏɴᴀᴛᴇ', callback_data='donate')]
]

# =================== Start Function =================== #

@Client.on_message(filters.private & filters.command(['start']))
async def start(client, message):
    user = message.from_user
    
    # Force Subscription Logic
    if Config.FORCE_SUB_ON == "True":
        try:
            # Extract username or ID from URL
            channel = Config.FORCE_SUB_CHANNEL.split('/')[-1]
            member = await client.get_chat_member(channel, user.id)
            if member.status == enums.ChatMemberStatus.BANNED:
                return await message.reply_text("❌ You are banned from using this bot.")
        except Exception:
            join_button = [
                [InlineKeyboardButton("ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=f"{Config.FORCE_SUB_CHANNEL}")],
                [InlineKeyboardButton("↻ ᴛʀʏ ᴀɢᴀɪɴ", url=f"https://t.me/{client.username}?start=start")]
            ]
            return await message.reply_text(
                "<b>ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ.</b>",
                reply_markup=InlineKeyboardMarkup(join_button)
            )

    # User registration in Database
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.mention)
        await client.send_message(
            chat_id=Config.LOG_CHANNEL,
            text=f"<b>#NewUser</b>\n\n<b>ID:</b> <code>{user.id}</code>\n<b>Name:</b> {user.mention}"
        )
    
    await message.reply_text(
        text=Translation.START_TXT.format(user.first_name),
        reply_markup=InlineKeyboardMarkup(main_buttons)
    )

# ================== Restart Function ================== #

@Client.on_message(filters.private & filters.command(['restart']) & filters.user(Config.BOT_OWNER_ID))
async def restart(client, message):
    msg = await message.reply_text("<i>ᴛʀʏɪɴɢ ᴛᴏ ʀᴇsᴛᴀʀᴛ sᴇʀᴠᴇʀ...</i>")
    await asyncio.sleep(2)
    await msg.edit("<b>sᴇʀᴠᴇʀ ʀᴇsᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ ✅</b>")
    os.execl(sys.executable, sys.executable, *sys.argv)

# ================== Callback Functions ================== #

@Client.on_callback_query(filters.regex(r'^help'))
async def helpcb(bot, query):
    await query.message.edit_text(
        text=Translation.HELP_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('• ʜᴏᴡ ᴛᴏ ᴜsᴇ ᴍᴇ ❓', callback_data='how_to_use')],
            [InlineKeyboardButton('• sᴇᴛᴛɪɴɢs ', callback_data='settings#main'), InlineKeyboardButton('• sᴛᴀᴛᴜs ', callback_data='status')],
            [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='back'), InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about')]
        ])
    )

@Client.on_callback_query(filters.regex(r'^how_to_use'))
async def how_to_use(bot, query):
    await query.message.edit_text(
        text=Translation.HOW_USE_TXT,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='help')]]),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r'^back'))
async def back(bot, query):
    await query.message.edit_text(
       text=Translation.START_TXT.format(query.from_user.first_name),
       reply_markup=InlineKeyboardMarkup(main_buttons)
    )

@Client.on_callback_query(filters.regex(r'^about'))
async def about(bot, query):
    await query.message.edit_text(
        text=Translation.ABOUT_TXT,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='back')]]),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r'^donate'))
async def donate(bot, query):
    await query.message.edit_text(
        text=Translation.DONATE_TXT,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='back')]]),
        disable_web_page_preview=True
    )

# --- Uptime Calculation ---
START_TIME = datetime.datetime.now()

def format_uptime():
    uptime = datetime.datetime.now() - START_TIME
    days, remainder = divmod(uptime.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0: parts.append(f"{int(days)}d")
    if hours > 0: parts.append(f"{int(hours)}h")
    if minutes > 0: parts.append(f"{int(minutes)}m")
    parts.append(f"{int(seconds)}s")
    return ", ".join(parts)

@Client.on_callback_query(filters.regex(r'^status'))
async def status(bot, query):
    users_count, bots_count = await db.total_users_bots_count()
    total_channels = await db.total_channels()
    uptime = format_uptime()

    await query.message.edit_text(
        text=Translation.STATUS_TXT.format(users_count, bots_count, temp.forwardings),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='help'), InlineKeyboardButton('• sᴇʀᴠᴇʀ sᴛᴀᴛs', callback_data='server_status')]
        ])
    )

@Client.on_callback_query(filters.regex(r'^server_status'))
async def server_status(bot, query):
    ram = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent()
    uptime = format_uptime()

    await query.message.edit_text(
        text=Translation.SERVER_TXT.format(cpu, ram),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='status')]])
    )

# =================== Donate Command =================== #

@Client.on_message(filters.private & filters.command(['donate']))
async def donate_cmd(client, message):
    await message.reply_text(Translation.DONATE_TXT)
