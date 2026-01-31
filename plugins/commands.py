import os
import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant
from config import Config, temp
from database import db
from translation import Translation

# --- MULTI-FORCE SUB LOGIC ---
async def force_sub(bot, message):
    if not Config.FORCE_SUB_ON:
        return True
    
    user_id = message.from_user.id
    missing_channels = []
    
    # Iterate through all channels in the list
    for channel_id in Config.FORCE_SUB_CHANNELS:
        try:
            # Check if user is a member
            await bot.get_chat_member(channel_id, user_id)
        except UserNotParticipant:
            # Generate Invite Link if missing
            try:
                chat = await bot.get_chat(channel_id)
                link = chat.invite_link
                if not link:
                    link = await bot.export_chat_invite_link(channel_id)
                missing_channels.append((chat.title, link))
            except Exception as e:
                # Skip invalid channels to prevent blocking the user
                print(f"Force Sub Error for {channel_id}: {e}")
                continue
        except Exception:
            continue
            
    if not missing_channels:
        return True
    
    # Create Buttons for all missing channels
    buttons = []
    for title, link in missing_channels:
        buttons.append([InlineKeyboardButton(text=f"Join {title}", url=link)])
    
    # Try Again Button
    try:
        # Pass start args back if they exist
        start_arg = message.command[1] if len(message.command) > 1 else ""
        url = f"https://t.me/{bot.me.username}?start={start_arg}"
    except:
        url = f"https://t.me/{bot.me.username}?start"
        
    buttons.append([InlineKeyboardButton("🔄 Try Again", url=url)])

    await message.reply_text(
        "<b>⚠️ Access Denied!</b>\n\n<b>Please join our updates channels to use this bot.</b>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return False

# --- COMMAND HANDLERS ---

@Client.on_message(filters.private & filters.command(["start"]))
async def start(bot, message):
    if not await force_sub(bot, message):
        return
        
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
        
    txt = Translation.START_TXT.format(message.from_user.first_name)
    buttons = [
        [InlineKeyboardButton('• ʜᴇʟᴘ •', callback_data='help'),
         InlineKeyboardButton('• ᴀʙᴏᴜᴛ •', callback_data='about')],
        [InlineKeyboardButton('• sᴇᴛᴛɪɴɢs •', callback_data='settings#main')],
        [InlineKeyboardButton('• ᴅᴏɴᴀᴛᴇ •', callback_data='donate')]
    ]
    await message.reply_text(text=txt, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_message(filters.private & filters.command(["live"]))
async def live_command(bot, message):
    if not await force_sub(bot, message):
        return
        
    # Redirect to the Live Settings Menu
    buttons = [[InlineKeyboardButton('⚙️ Setup Live Forwarding', callback_data='settings#live')]]
    await message.reply_text(
        "<b><u>📡 Live Auto-Forwarding</u></b>\n\nThis feature allows you to forward messages in real-time from a source channel to multiple destination channels.\n\nClick below to configure your tasks.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.private & filters.command(["help"]))
async def help_command(bot, message):
    if not await force_sub(bot, message):
        return
    await message.reply_text(
        text=Translation.HELP_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('• ʜᴏᴡ ᴛᴏ ᴜsᴇ •', callback_data='how_to_use')],
            [InlineKeyboardButton('• ʙᴀᴄᴋ •', callback_data='start')]
        ])
    )

@Client.on_message(filters.private & filters.command(["donate"]))
async def donate_command(bot, message):
    await message.reply_text(
        text=Translation.DONATE_TXT,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('• ʙᴀᴄᴋ •', callback_data='start')]])
    )

@Client.on_message(filters.private & filters.command(["status"]) & filters.user(Config.BOT_OWNER_ID))
async def status_command(bot, message):
    users, bots = await db.total_users_bots_count()
    # Count active tasks (approximate via locks)
    active = len([k for k, v in temp.lock.items() if v])
    # Count live tasks in DB
    live = await db.live.count_documents({})
    
    await message.reply_text(
        text=Translation.STATUS_TXT.format(users, bots, active, live)
    )

# --- CALLBACK HANDLERS ---

@Client.on_callback_query(filters.regex('^help$'))
async def help_cb(bot, query):
    await query.message.edit_text(
        text=Translation.HELP_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('• ʜᴏᴡ ᴛᴏ ᴜsᴇ •', callback_data='how_to_use')],
            [InlineKeyboardButton('• ʙᴀᴄᴋ •', callback_data='start')]
        ])
    )

@Client.on_callback_query(filters.regex('^how_to_use$'))
async def how_to_use_cb(bot, query):
    await query.message.edit_text(
        text=Translation.HOW_USE_TXT,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('• ʙᴀᴄᴋ •', callback_data='help')]])
    )

@Client.on_callback_query(filters.regex('^about$'))
async def about_cb(bot, query):
    await query.message.edit_text(
        text=Translation.ABOUT_TXT,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('• ʙᴀᴄᴋ •', callback_data='start')]])
    )

@Client.on_callback_query(filters.regex('^donate$'))
async def donate_cb(bot, query):
    await query.message.edit_text(
        text=Translation.DONATE_TXT,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('• ʙᴀᴄᴋ •', callback_data='start')]])
    )

@Client.on_callback_query(filters.regex('^start$'))
async def start_cb(bot, query):
    txt = Translation.START_TXT.format(query.from_user.first_name)
    buttons = [
        [InlineKeyboardButton('• ʜᴇʟᴘ •', callback_data='help'),
         InlineKeyboardButton('• ᴀʙᴏᴜᴛ •', callback_data='about')],
        [InlineKeyboardButton('• sᴇᴛᴛɪɴɢs •', callback_data='settings#main')],
        [InlineKeyboardButton('• ᴅᴏɴᴀᴛᴇ •', callback_data='donate')]
    ]
    await query.message.edit_text(text=txt, reply_markup=InlineKeyboardMarkup(buttons))
