import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config, temp
from database import db
from translation import Translation
from .utils import STS

@Client.on_message(filters.private & filters.command(["forward"]))
async def forward(bot, message):
    user_id = message.from_user.id
    
    # Check if user has an active task
    if temp.lock.get(user_id) and str(temp.lock.get(user_id)) == "True":
        return await message.reply("**Please wait until previous task completed.**")
    
    # Initialize Status Class for this user
    sts = STS(user_id)
    
    # Check if user has added a bot
    if not await db.is_bot_exist(user_id):
        return await message.reply("<b>You didn't add any bot. Please add a bot using /settings !</b>")

    # Step 1: Ask for Source Channel
    await message.reply(Translation.FROM_MSG)
    
    # Listen for Source Input
    try:
        source_msg = await bot.listen(chat_id=user_id, timeout=300)
        
        if source_msg.text == '/cancel':
            return await source_msg.reply(Translation.CANCEL)
        
        # Determine Source Chat ID and Last Message ID (Limit)
        if source_msg.forward_from_chat:
            chat_id = source_msg.forward_from_chat.id
            limit = source_msg.forward_from_message_id
        else:
            # Handle Link input (e.g., https://t.me/channel/1234)
            if source_msg.text and "https://t.me/" in source_msg.text:
                try:
                    parts = source_msg.text.split('/')
                    # For private channels with -100 ID logic if needed, 
                    # but usually links give username or ID part
                    if parts[-2].isdigit(): # /c/12345/123 style
                         chat_id = int(f"-100{parts[-2]}")
                    else:
                         chat_id = parts[-2] # username
                    limit = int(parts[-1])
                except:
                     return await source_msg.reply("<b>Invalid Link Format. Use a valid message link.</b>")
            else:
                return await source_msg.reply("<b>Please Forward a message or send a message Link.</b>")

        # Step 2: Select Target Channel
        # [FIX] Using .set() instead of .add() to safely initialize data without KeyError
        sts.set('FROM', chat_id)
        sts.set('limit', limit)
        
        # Generate Target Channel Buttons
        buttons = []
        user_channels = await db.get_user_channels(user_id)
        
        for channel in user_channels:
            buttons.append([InlineKeyboardButton(
                text=channel['title'], 
                callback_data=f"fwd_target#{channel['chat_id']}#{channel['title']}"
            )])
            
        buttons.append([InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', callback_data='cancel_fwd')])
        
        await message.reply(
            Translation.TO_MSG,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except asyncio.exceptions.TimeoutError:
        await message.reply("<b>Process Timeout. Please start again.</b>")
    except Exception as e:
        await message.reply(f"<b>Error:</b> {e}")


@Client.on_callback_query(filters.regex(r'^fwd_target'))
async def target_selection(bot, query):
    user_id = query.from_user.id
    data = query.data.split('#')
    target_id = int(data[1])
    target_title = data[2]
    
    sts = STS(user_id)
    
    # Store Target (For Bulk, we handle 1 target at a time here)
    # [FIX] Using .set() here as well
    sts.set('TO', target_id)
    
    await query.message.delete()
    
    # Step 3: Ask for Skip Count
    ask_skip = await bot.ask(
        user_id, 
        Translation.SKIP_MSG, 
        filters=filters.text,
        timeout=300
    )
    
    if ask_skip.text == '/cancel':
        return await ask_skip.reply(Translation.CANCEL)
        
    try:
        skip_count = int(ask_skip.text)
    except ValueError:
        skip_count = 0 # Default to 0 if invalid
        
    # Store Final Data
    # STS.store saves: FROM, TO, skip, limit, etc.
    # It calculates 'total' as limit - skip
    sts.store(sts.get('FROM'), target_id, skip_count, sts.get('limit'))
    
    # Fetch Data for Confirmation
    data = sts.get(full=True)
    bot_data = await db.get_bot(user_id)
    
    # Step 4: Double Check Message
    # Using the Translation template we updated earlier
    text = Translation.DOUBLE_CHECK.format(
        botname=bot_data['name'],
        from_chat=data.FROM,
        to_chat=target_title,
        skip=skip_count
    )
    
    buttons = [
        [InlineKeyboardButton('✅ ʏᴇs, sᴛᴀʀᴛ', callback_data=f'start_public_forward_{user_id}')],
        [InlineKeyboardButton('❌ ɴᴏ, ᴄᴀɴᴄᴇʟ', callback_data='cancel_fwd')]
    ]
    
    await ask_skip.reply(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex('^cancel_fwd'))
async def cancel_fwd(bot, query):
    await query.message.edit(Translation.CANCEL)
