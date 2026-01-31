import asyncio 
from database import db
from config import Config, temp
from translation import Translation
from pyrogram import Client, filters
from .test import get_configs, update_configs, CLIENT, parse_buttons
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CLIENT = CLIENT()

@Client.on_message(filters.command('settings'))
async def settings(client, message):
   await message.delete()
   await message.reply_text(
     "<b>cʜᴀɴɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ᴀs ʏᴏᴜʀ ᴡɪsʜ.</b>",
     reply_markup=main_buttons()
     )
    
@Client.on_callback_query(filters.regex(r'^settings'))
async def settings_query(bot, query):
  user_id = query.from_user.id
  i, type = query.data.split("#")
  buttons = [[InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data="settings#main")]]
  
  if type=="main":
     await query.message.edit_text(
       "<b>cʜᴀɴɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ᴀs ʏᴏᴜʀ ᴡɪsʜ.</b>",
       reply_markup=main_buttons())
       
  elif type=="bots":
     buttons = [] 
     _bot = await db.get_bot(user_id)
     if _bot is not None:
        buttons.append([InlineKeyboardButton(_bot['name'],
                         callback_data=f"settings#editbot")])
        buttons.append([InlineKeyboardButton('✚ ᴀᴅᴅ ᴜsᴇʀ ʙᴏᴛ ✚', 
                         callback_data="settings#adduserbot")])
        buttons.append([InlineKeyboardButton('✚ ʟᴏɢɪɴ ᴜsᴇʀ ʙᴏᴛ ✚', 
                         callback_data="settings#addlogin")])
     else:
        buttons.append([InlineKeyboardButton('✚ ᴀᴅᴅ ʙᴏᴛ ✚', 
                         callback_data="settings#addbot")])
        buttons.append([InlineKeyboardButton('✚ ᴀᴅᴅ ᴜsᴇʀ ʙᴏᴛ ✚', 
                         callback_data="settings#adduserbot")])
        buttons.append([InlineKeyboardButton('✚ ʟᴏɢɪɴ ᴜsᴇʀ ʙᴏᴛ ✚', 
                         callback_data="settings#addlogin")])
     buttons.append([InlineKeyboardButton('• ʙᴀᴄᴋ', 
                      callback_data="settings#main")])
     await query.message.edit_text(
       "<b><u>ᴍʏ ʙᴏᴛs</b></u>\n\n<b>ʏᴏᴜ ᴄᴀɴ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ᴀʟʟ ʙᴏᴛ ғʀᴏᴍ ʜᴇʀᴇ</b>",
       reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="addbot":
     await query.message.delete()
     bot = await CLIENT.add_bot(bot, query)
     if bot != True: return
     await query.message.reply_text(
        "<b>ʙᴏᴛ ᴛᴏᴋᴇɴ sᴜᴄᴄᴇssғᴜʟʟʏ ᴀᴅᴅᴇᴅ ᴛᴏ ᴅʙ ✅</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type == "addlogin":
     await query.message.delete()
     user = await CLIENT.add_login(bot, query)
     if user is None: return    
     await query.message.reply_text(
        "<b>sᴜᴄᴄᴇssғᴜʟʟʏ ʟᴏɢɪɴ ᴛᴏ ᴅʙ ✅</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
        
  elif type=="adduserbot":
     await query.message.delete()
     user = await CLIENT.add_session(bot, query)
     if user != True: return
     await query.message.reply_text(
        "<b>sᴇssɪᴏɴ sᴜᴄᴄᴇss ғᴜʟʟʏ ᴀᴅᴅᴇᴅ ᴛᴏ ᴅʙ ✅</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
      
  elif type=="channels":
     buttons = []
     channels = await db.get_user_channels(user_id)
     for channel in channels:
        buttons.append([InlineKeyboardButton(f"{channel['title']}",
                         callback_data=f"settings#editchannels_{channel['chat_id']}")])
     buttons.append([InlineKeyboardButton('✚ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ ✚', 
                      callback_data="settings#addchannel")])
     buttons.append([InlineKeyboardButton('• ʙᴀᴄᴋ', 
                      callback_data="settings#main")])
     await query.message.edit_text( 
       "<b><u>ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟs</b></u>\n\n<b>ʏᴏᴜ ᴄᴀɴ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ᴛᴀʀɢᴇᴛ ᴄʜᴀᴛ ʜᴇʀᴇ ‼️</b>",
       reply_markup=InlineKeyboardMarkup(buttons))
   
  elif type=="addchannel":  
     await query.message.delete()
     try:
         text = await bot.send_message(user_id, "<b>sᴇᴛ ᴛᴀʀɢᴇᴛ ᴄʜᴀɴɴᴇʟ\n\nғᴏʀᴡᴀʀᴅ ᴀ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴛᴀʀɢᴇᴛ ᴄʜᴀɴɴᴇʟ.\n/cancel - ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜɪs ᴘʀᴏᴄᴇss</b>")
         chat_ids = await bot.listen(chat_id=user_id, timeout=300)
         if chat_ids.text=="/cancel":
            await chat_ids.delete()
            return await text.edit_text(
                  "<b>ᴘʀᴏᴄᴇss ᴄᴀɴᴄᴇʟʟᴇᴅ</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
         elif not chat_ids.forward_date:
            await chat_ids.delete()
            return await text.edit_text("**ᴛʜɪs ɪs ɴᴏᴛ ᴀ ғᴏʀᴡᴀʀᴅᴇᴅ ᴍᴇssᴀɢᴇ**")
         else:
            chat_id = chat_ids.forward_from_chat.id
            title = chat_ids.forward_from_chat.title
            username = chat_ids.forward_from_chat.username
            username = "@" + username if username else "private"
         chat = await db.add_channel(user_id, chat_id, title, username)
         await chat_ids.delete()
         await text.edit_text(
            "<b>sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ✅</b>" if chat else "<b>ᴛʜɪs ᴄʜᴀɴɴᴇʟ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴅᴅᴇᴅ</b>",
            reply_markup=InlineKeyboardMarkup(buttons))
     except asyncio.exceptions.TimeoutError:
         await text.edit_text('ᴘʀᴏᴄᴇss ʜᴀs ʙᴇᴇɴ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴄᴀɴᴄᴇʟʟᴇᴅ.', reply_markup=InlineKeyboardMarkup(buttons))

  elif type=="editbot": 
     bot_data = await db.get_bot(user_id)
     TEXT = Translation.BOT_DETAILS if bot_data['is_bot'] else Translation.USER_DETAILS
     buttons = [[InlineKeyboardButton('❌ ʀᴇᴍᴏᴠᴇ ❌', callback_data=f"settings#removebot")
               ],
               [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data="settings#bots")]]
     await query.message.edit_text(
        TEXT.format(bot_data['name'], bot_data['id'], bot_data['username']),
        reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type=="removebot":
     await db.remove_bot(user_id)
     await query.message.edit_text(
        "<b>sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ✅</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type.startswith("editchannels"): 
     chat_id = type.split('_')[1]
     chat = await db.get_channel_details(user_id, chat_id)
     buttons = [[InlineKeyboardButton('❌ ʀᴇᴍᴏᴠᴇ ❌', callback_data=f"settings#removechannel_{chat_id}")
               ],
               [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data="settings#channels")]]
     await query.message.edit_text(
        f"<b><u>📄 ᴄʜᴀɴɴᴇʟ ᴅᴇᴛᴀɪʟs</b></u>\n\n<b>- ᴛɪᴛʟᴇ:</b> <code>{chat['title']}</code>\n<b>- ᴄʜᴀɴɴᴇʟ ɪᴅ: </b> <code>{chat['chat_id']}</code>\n<b>- ᴜsᴇʀɴᴀᴍᴇ:</b> {chat['username']}",
        reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type.startswith("removechannel"):
     chat_id = type.split('_')[1]
     await db.remove_channel(user_id, chat_id)
     await query.message.edit_text(
        "<b>sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ✅</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
                               
  elif type=="caption":
     buttons = []
     data = await get_configs(user_id)
     caption = data['caption']
     if caption is None:
        buttons.append([InlineKeyboardButton('✚ ᴀᴅᴅ ᴄᴀᴘᴛɪᴏɴ ✚', 
                      callback_data="settings#addcaption")])
     else:
        buttons.append([InlineKeyboardButton('sᴇᴇ ᴄᴀᴘᴛɪᴏɴ', 
                      callback_data="settings#seecaption")])
        buttons[-1].append(InlineKeyboardButton('🗑️ ᴅᴇʟᴇᴛᴇ ᴄᴀᴘᴛɪᴏɴ', 
                      callback_data="settings#deletecaption"))
     buttons.append([InlineKeyboardButton('• ʙᴀᴄᴋ', 
                      callback_data="settings#main")])
     await query.message.edit_text(
        "<b><u>CUSTOM CAPTION</b></u>\n\n<b>You can set a custom caption to videos and documents. Normaly use its default caption</b>\n\n<b><u>AVAILABLE FILLINGS:</b></u>\n- <code>{filename}</code> : Filename\n- <code>{size}</code> : File size\n- <code>{caption}</code> : default caption",
        reply_markup=InlineKeyboardMarkup(buttons))
                               
  elif type=="seecaption":   
     data = await get_configs(user_id)
     buttons = [[InlineKeyboardButton('🖋️ ᴇᴅɪᴛ ᴄᴀᴘᴛɪᴏɴ', 
                  callback_data="settings#addcaption")
               ],[
               InlineKeyboardButton('• ʙᴀᴄᴋ', 
                 callback_data="settings#caption")]]
     await query.message.edit_text(
        f"<b><u>YOUR CUSTOM CAPTION</b></u>\n\n<code>{data['caption']}</code>",
        reply_markup=InlineKeyboardMarkup(buttons))
    
  elif type=="deletecaption":
     await update_configs(user_id, 'caption', None)
     await query.message.edit_text(
        "<b>successfully updated</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
                              
  elif type=="addcaption":
     await query.message.delete()
     try:
         text = await bot.send_message(query.message.chat.id, "Send your custom caption\n/cancel - <code>cancel this process</code>")
         caption = await bot.listen(chat_id=user_id, timeout=300)
         if caption.text=="/cancel":
            await caption.delete()
            return await text.edit_text(
                  "<b>process canceled !</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
         try:
            caption.text.format(filename='', size='', caption='')
         except KeyError as e:
            await caption.delete()
            return await text.edit_text(
               f"<b>wrong filling {e} used in your caption. change it</b>",
               reply_markup=InlineKeyboardMarkup(buttons))
         await update_configs(user_id, 'caption', caption.text)
         await caption.delete()
         await text.edit_text(
            "<b>Successfully Updated</b>",
            reply_markup=InlineKeyboardMarkup(buttons))
     except asyncio.exceptions.TimeoutError:
         await text.edit_text('Process has been automatically cancelled', reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="button":
     buttons = []
     button = (await get_configs(user_id))['button']
     if button is None:
        buttons.append([InlineKeyboardButton('✚ ᴀᴅᴅ ʙᴜᴛᴛᴏɴ ✚', 
                      callback_data="settings#addbutton")])
     else:
        buttons.append([InlineKeyboardButton('👀 sᴇᴇ ʙᴜᴛᴛᴏɴ', 
                      callback_data="settings#seebutton")])
        buttons[-1].append(InlineKeyboardButton('🗑️ ʀᴇᴍᴏᴠᴇ ʙᴜᴛᴛᴏɴ ', 
                      callback_data="settings#deletebutton"))
     buttons.append([InlineKeyboardButton('↩ Back', 
                      callback_data="settings#main")])
     await query.message.edit_text(
        "<b><u>CUSTOM BUTTON</b></u>\n\n<b>You can set a inline button to messages.</b>\n\n<b><u>FORMAT:</b></u>\n`[Forward bot][buttonurl:https://t.me/PurelySin]`\n",
        reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="addbutton":
     await query.message.delete()
     try:
         txt = await bot.send_message(user_id, text="**Send your custom button.\n\nFORMAT:**\n`[AkMovieVerse][buttonurl:https://t.me/AkMovieVerse]`\n")
         ask = await bot.listen(chat_id=user_id, timeout=300)
         button = parse_buttons(ask.text.html)
         if not button:
            await ask.delete()
            return await txt.edit_text("**INVALID BUTTON**")
         await update_configs(user_id, 'button', ask.text.html)
         await ask.delete()
         await txt.edit_text("**Successfully button added**",
            reply_markup=InlineKeyboardMarkup(buttons))
     except asyncio.exceptions.TimeoutError:
         await txt.edit_text('Process has been automatically cancelled', reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="seebutton":
      button_text = (await get_configs(user_id))['button']
      button_markup = parse_buttons(button_text, markup=False)
      button_markup.append([InlineKeyboardButton("↩ Back", "settings#button")])
      await query.message.edit_text(
         "**YOUR CUSTOM BUTTON**",
         reply_markup=InlineKeyboardMarkup(button_markup))
      
  elif type=="deletebutton":
     await update_configs(user_id, 'button', None)
     await query.message.edit_text(
        "**Successfully button deleted**",
        reply_markup=InlineKeyboardMarkup(buttons))
   
  elif type=="database":
     buttons = []
     db_uri = (await get_configs(user_id))['db_uri']
     if db_uri is None:
        buttons.append([InlineKeyboardButton('✚ ᴀᴅᴅ ᴜʀʟ ✚', 
                      callback_data="settings#addurl")])
     else:
        buttons.append([InlineKeyboardButton('👀 sᴇᴇ ᴜʀʟ', 
                      callback_data="settings#seeurl")])
        buttons[-1].append(InlineKeyboardButton('🗑️ ʀᴇᴍᴏᴠᴇ ᴜʀʟ ', 
                      callback_data="settings#deleteurl"))
     buttons.append([InlineKeyboardButton('• ʙᴀᴄᴋ', 
                      callback_data="settings#main")])
     await query.message.edit_text(
        "<b><u>DATABASE</u>\n\nDatabase is required for store your duplicate messages permenant. other wise stored duplicate media may be disappeared when after bot restart.</b>",
        reply_markup=InlineKeyboardMarkup(buttons))

  elif type=="addurl":
     await query.message.delete()
     uri = await bot.ask(user_id, "<b>please send your mongodb url.</b>\n\n<i>get your Mongodb url from [here](https://mongodb.com)</i>", disable_web_page_preview=True)
     if uri.text=="/cancel":
        return await uri.reply_text(
                  "<b>process canceled !</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
     if not uri.text.startswith("mongodb+srv://") and not uri.text.endswith("majority"):
        return await uri.reply("<b>Invalid Mongodb Url</b>",
                   reply_markup=InlineKeyboardMarkup(buttons))
     await update_configs(user_id, 'db_uri', uri.text)
     await uri.reply("**Successfully database url added**",
             reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="seeurl":
     db_uri = (await get_configs(user_id))['db_uri']
     await query.answer(f"DATABASE URL: {db_uri}", show_alert=True)
  
  elif type=="deleteurl":
     await update_configs(user_id, 'db_uri', None)
     await query.message.edit_text(
        "**Successfully your database url deleted**",
        reply_markup=InlineKeyboardMarkup(buttons))
      
  elif type=="filters":
     await query.message.edit_text(
        "<b><u>💠 CUSTOM FILTERS 💠</b></u>\n\n**configure the type of messages which you want forward**",
        reply_markup=await filters_buttons(user_id))
  
  elif type=="nextfilters":
     await query.edit_message_reply_markup( 
        reply_markup=await next_filters_buttons(user_id))
   
  elif type.startswith("updatefilter"):
     i, key, value = type.split('-')
     if value=="True":
        await update_configs(user_id, key, False)
     else:
        await update_configs(user_id, key, True)
     if key in ['poll', 'protect']:
        return await query.edit_message_reply_markup(
           reply_markup=await next_filters_buttons(user_id)) 
     await query.edit_message_reply_markup(
        reply_markup=await filters_buttons(user_id))
   
  elif type.startswith("file_size"):
    settings_data = await get_configs(user_id)
    size = settings_data.get('file_size', 0)
    i, limit = size_limit(settings_data['size_limit'])
    await query.message.edit_text(
       f'<b><u>SIZE LIMIT</b></u><b>\n\nyou can set file size limit to forward\n\nStatus: files with {limit} `{size} MB` will forward</b>',
       reply_markup=size_button(size))
  
  elif type.startswith("update_size"):
    size = int(query.data.split('-')[1])
    if 0 < size > 2000:
      return await query.answer("size limit exceeded", show_alert=True)
    await update_configs(user_id, 'file_size', size)
    i, limit = size_limit((await get_configs(user_id))['size_limit'])
    await query.message.edit_text(
       f'<b><u>SIZE LIMIT</b></u><b>\n\nyou can set file size limit to forward\n\nStatus: files with {limit} `{size} MB` will forward</b>',
       reply_markup=size_button(size))
  
  elif type.startswith('update_limit'):
    i, limit, size = type.split('-')
    limit, sts_text = size_limit(limit)
    await update_configs(user_id, 'size_limit', limit) 
    await query.message.edit_text(
       f'<b><u>SIZE LIMIT</b></u><b>\n\nyou can set file size limit to forward\n\nStatus: files with {sts_text} `{size} MB` will forward</b>',
       reply_markup=size_button(int(size)))
       
  elif type == "add_extension":
    await query.message.delete() 
    ext = await bot.ask(user_id, text="**please send your extensions (seperete by space)**")
    if ext.text == '/cancel':
       return await ext.reply_text(
                  "<b>process canceled</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
    extensions = ext.text.split(" ")
    extension = (await get_configs(user_id))['extension']
    if extension:
        for extn in extensions:
            extension.append(extn)
    else:
        extension = extensions
    await update_configs(user_id, 'extension', extension)
    await ext.reply_text(
        f"**successfully updated**",
        reply_markup=InlineKeyboardMarkup(buttons))
       
  elif type == "get_extension":
    extensions = (await get_configs(user_id))['extension']
    btn = extract_btn(extensions)
    btn.append([InlineKeyboardButton('✚ ᴀᴅᴅ ✚', 'settings#add_extension')])
    btn.append([InlineKeyboardButton('ʀᴇᴍᴏᴠᴇ ᴀʟʟ', 'settings#rmve_all_extension')])
    btn.append([InlineKeyboardButton('• ʙᴀᴄᴋ', 'settings#main')])
    await query.message.edit_text(
        text='<b><u>EXTENSIONS</u></b>\n\n**Files with these extiontions will not forward**',
        reply_markup=InlineKeyboardMarkup(btn))
  
  elif type == "rmve_all_extension":
    await update_configs(user_id, 'extension', None)
    await query.message.edit_text(text="**sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ**",
                                   reply_markup=InlineKeyboardMarkup(buttons))
  elif type == "add_keyword":
    await query.message.delete()
    ask = await bot.ask(user_id, text="**ᴘʟᴇᴀsᴇ sᴇɴᴛ ᴋᴇʏᴡᴏʀᴅ (sᴇᴘʀᴀᴛᴇᴅ ʙʏ sᴘᴀᴄᴇ)**")
    if ask.text == '/cancel':
       return await ask.reply_text(
                  "<b>ᴘʀᴏᴄᴇss ᴄᴀɴᴄᴇʟʟᴇᴅ ✅</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
    keywords = ask.text.split(" ")
    keyword = (await get_configs(user_id))['keywords']
    if keyword:
        for word in keywords:
            keyword.append(word)
    else:
        keyword = keywords
    await update_configs(user_id, 'keywords', keyword)
    await ask.reply_text(
        f"**successfully updated**",
        reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type == "get_keyword":
    keywords = (await get_configs(user_id))['keywords']
    btn = extract_btn(keywords)
    btn.append([InlineKeyboardButton('✚ ᴀᴅᴅ ✚', 'settings#add_keyword')])
    btn.append([InlineKeyboardButton('ʀᴇᴍᴏᴠᴇ ᴀʟʟ', 'settings#rmve_all_keyword')])
    btn.append([InlineKeyboardButton('• ʙᴀᴄᴋ', 'settings#main')])
    await query.message.edit_text(
        text='<b><u>KEYWORDS</u></b>\n\n**File with these keywords in file name will forwad**',
        reply_markup=InlineKeyboardMarkup(btn))
      
  elif type == "rmve_all_keyword":
    await update_configs(user_id, 'keywords', None)
    await query.message.edit_text(text="**sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ**",
                                   reply_markup=InlineKeyboardMarkup(buttons))
  elif type.startswith("alert"):
    alert = type.split('_')[1]
    await query.answer(alert, show_alert=True)
    
  # --- NEW FEATURES HANDLERS ---
  
  elif type == "replace":
     config = await get_configs(user_id)
     text = f"{Translation.REPLACE_TXT}\n\n<b>Current:</b> <code>{config['replace_text']}</code>"
     buttons = [[InlineKeyboardButton('🖋️ sᴇᴛ ʀᴇᴘʟᴀᴄᴇ ʟɪsᴛ', 'settings#add_replace')],
                [InlineKeyboardButton('🗑️ ʀᴇᴍᴏᴠᴇ ᴀʟʟ', 'settings#del_replace')],
                [InlineKeyboardButton('• ʙᴀᴄᴋ', 'settings#main')]]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "add_replace":
     await query.message.delete()
     ask = await bot.ask(user_id, "Send replace list in <code>old|new, old2|new2</code> format.")
     if ask.text == "/cancel": return await ask.reply("Cancelled.", reply_markup=InlineKeyboardMarkup(buttons))
     await update_configs(user_id, 'replace_text', ask.text)
     await ask.reply("Updated Successfully!", reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "del_replace":
     await update_configs(user_id, 'replace_text', None)
     await query.message.edit_text("Deleted!", reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "remove_text":
     config = await get_configs(user_id)
     text = f"{Translation.REMOVE_TXT}\n\n<b>Current:</b> <code>{config['remove_text']}</code>"
     buttons = [[InlineKeyboardButton('🖋️ sᴇᴛ ʀᴇᴍᴏᴠᴇ ʟɪsᴛ', 'settings#add_remove')],
                [InlineKeyboardButton('🗑️ ʀᴇᴍᴏᴠᴇ ᴀʟʟ', 'settings#del_remove')],
                [InlineKeyboardButton('• ʙᴀᴄᴋ', 'settings#main')]]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "add_remove":
     await query.message.delete()
     ask = await bot.ask(user_id, "Send words to remove separated by space.")
     if ask.text == "/cancel": return await ask.reply("Cancelled.", reply_markup=InlineKeyboardMarkup(buttons))
     await update_configs(user_id, 'remove_text', ask.text)
     await ask.reply("Updated Successfully!", reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "del_remove":
     await update_configs(user_id, 'remove_text', None)
     await query.message.edit_text("Deleted!", reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "thumb":
     config = await get_configs(user_id)
     status = "ENABLED ✅" if config['thumb_toggle'] else "DISABLED ❌"
     text = f"{Translation.THUMB_TXT}\n\n<b>Status:</b> {status}"
     buttons = [[InlineKeyboardButton('🖼️ sᴇᴛ ᴛʜᴜᴍʙ', 'settings#add_thumb'),
                 InlineKeyboardButton('🗑️ ᴅᴇʟ ᴛʜᴜᴍʙ', 'settings#del_thumb')],
                [InlineKeyboardButton('🔄 ᴛᴏɢɢʟᴇ', f"settings#toggle_thumb-{config['thumb_toggle']}")],
                [InlineKeyboardButton('• ʙᴀᴄᴋ', 'settings#main')]]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "add_thumb":
     await query.message.delete()
     ask = await bot.ask(user_id, "Please send the photo for your custom thumbnail.")
     if ask.photo:
         await update_configs(user_id, 'thumbnail', ask.photo.file_id)
         await ask.reply("Thumbnail Saved!", reply_markup=InlineKeyboardMarkup(buttons))
     else: await ask.reply("Not a photo!", reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "del_thumb":
     await update_configs(user_id, 'thumbnail', None)
     await query.message.edit_text("Thumbnail Removed!", reply_markup=InlineKeyboardMarkup(buttons))

  elif type.startswith("toggle_thumb"):
     val = type.split('-')[1] == "True"
     await update_configs(user_id, 'thumb_toggle', not val)
     await settings_query(bot, query) # Refresh menu

  elif type == "workers":
     config = await get_configs(user_id)
     curr = config['workers']
     text = f"<b><u>WORKER MANAGEMENT</u></b>\n\nWorkers allow you to use multiple sessions at once for faster forwarding.\n\n<b>Current Workers:</b> {curr}"
     buttons = [[InlineKeyboardButton('-', f'settings#upd_work-{curr-1}'),
                 InlineKeyboardButton('+', f'settings#upd_work-{curr+1}')],
                [InlineKeyboardButton('• ʙᴀᴄᴋ', 'settings#main')]]
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

  elif type.startswith("upd_work"):
     val = int(type.split('-')[1])
     if val < 1 or val > 10: return await query.answer("Limit: 1 to 10", show_alert=True)
     await update_configs(user_id, 'workers', val)
     await settings_query(bot, query)

  elif type == "live":
     buttons = []
     tasks = await db.get_live_tasks()
     # Simple list of live sources managed by user
     # For production, filter tasks by user_id if needed
     buttons.append([InlineKeyboardButton('✚ ᴀᴅᴅ ʟɪᴠᴇ ᴛᴀsᴋ', 'settings#add_live')])
     buttons.append([InlineKeyboardButton('• ʙᴀᴄᴋ', 'settings#main')])
     await query.message.edit_text("<b><u>LIVE FORWARDING</u></b>\n\nManage your auto-post tasks here.", reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "add_live":
     await query.message.delete()
     src = await bot.ask(user_id, "Forward last message from SOURCE channel.")
     if not src.forward_from_chat: return await src.reply("Invalid.")
     source = src.forward_from_chat.id
     tgt = await bot.ask(user_id, "Send TARGET IDs separated by space (Max 5).")
     targets = [int(x) for x in tgt.text.split()]
     await db.add_live_task(user_id, source, targets[:5])
     await tgt.reply("Live Task Added!", reply_markup=InlineKeyboardMarkup(buttons))

def main_buttons():
  buttons = [[
       InlineKeyboardButton('🤖 ʙᴏᴛs', callback_data='settings#bots'),
       InlineKeyboardButton('🏷 ᴄʜᴀɴɴᴇʟs', callback_data='settings#channels')
       ],[
       InlineKeyboardButton('🖋️ ᴄᴀᴘᴛɪᴏɴ', callback_data='settings#caption'),
       InlineKeyboardButton('🗃 ᴍᴏɴɢᴏ ᴅʙ', callback_data='settings#database')
       ],[
       InlineKeyboardButton('🕵‍♀️ ғɪʟᴛᴇʀs 🕵‍♀️', callback_data='settings#filters'),
       InlineKeyboardButton('⏹ ʙᴜᴛᴛᴏɴ', callback_data='settings#button')
       ],[
       InlineKeyboardButton('📡 ʟɪᴠᴇ ғᴡᴅ', callback_data='settings#live'),
       InlineKeyboardButton('👷 ᴡᴏʀᴋᴇʀs', callback_data='settings#workers')
       ],[
       InlineKeyboardButton('🔄 ʀᴇᴘʟᴀᴄᴇ', callback_data='settings#replace'),
       InlineKeyboardButton('🗑 ʀᴇᴍᴏᴠᴇ', callback_data='settings#remove_text')
       ],[
       InlineKeyboardButton('🖼 ᴛʜᴜᴍʙɴᴀɪʟ', callback_data='settings#thumb'),
       InlineKeyboardButton('🧪 ᴇxᴛʀᴀ sᴇᴛs', callback_data='settings#nextfilters')
       ],[      
       InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='help')
       ]]
  return InlineKeyboardMarkup(buttons)

def size_limit(limit):
   if str(limit) == "None":
      return None, ""
   elif str(limit) == "True":
      return True, "more than"
   else:
      return False, "less than"

def extract_btn(datas):
    i = 0
    btn = []
    if datas:
       for data in datas:
         if i >= 5:
            i = 0
         if i == 0:
            btn.append([InlineKeyboardButton(data, f'settings#alert_{data}')])
            i += 1
            continue
         elif i > 0:
            btn[-1].append(InlineKeyboardButton(data, f'settings#alert_{data}'))
            i += 1
    return btn 

def size_button(size):
  buttons = [[
       InlineKeyboardButton('+', callback_data=f'settings#update_limit-True-{size}'),
       InlineKeyboardButton('=', callback_data=f'settings#update_limit-None-{size}'),
       InlineKeyboardButton('-', callback_data=f'settings#update_limit-False-{size}')
       ],[
       InlineKeyboardButton('+1', callback_data=f'settings#update_size-{size + 1}'),
       InlineKeyboardButton('-1', callback_data=f'settings#update_size_-{size - 1}')
       ],[
       InlineKeyboardButton('+5', callback_data=f'settings#update_size-{size + 5}'),
       InlineKeyboardButton('-5', callback_data=f'settings#update_size_-{size - 5}')
       ],[
       InlineKeyboardButton('+10', callback_data=f'settings#update_size-{size + 10}'),
       InlineKeyboardButton('-10', callback_data=f'settings#update_size_-{size - 10}')
       ],[
       InlineKeyboardButton('+50', callback_data=f'settings#update_size-{size + 50}'),
       InlineKeyboardButton('-50', callback_data=f'settings#update_size_-{size - 50}')
       ],[
       InlineKeyboardButton('+100', callback_data=f'settings#update_size-{size + 100}'),
       InlineKeyboardButton('-100', callback_data=f'settings#update_size_-{size - 100}')
       ],[
       InlineKeyboardButton('↩ Back', callback_data="settings#main")
     ]]
  return InlineKeyboardMarkup(buttons)
       
async def filters_buttons(user_id):
  config_data = await get_configs(user_id)
  filters_data = config_data['filters']
  buttons = [[
       InlineKeyboardButton('🏷️ ғᴏʀᴡᴀʀᴅ ᴛᴀɢ', callback_data=f'settings_#updatefilter-forward_tag-{config_data["forward_tag"]}'),
       InlineKeyboardButton('✅' if config_data['forward_tag'] else '❌', callback_data=f'settings#updatefilter-forward_tag-{config_data["forward_tag"]}')
       ],[
       InlineKeyboardButton('🖍️ ᴛᴇxᴛ', callback_data=f'settings_#updatefilter-text-{filters_data["text"]}'),
       InlineKeyboardButton('✅' if filters_data['text'] else '❌', callback_data=f'settings#updatefilter-text-{filters_data["text"]}')
       ],[
       InlineKeyboardButton('📁 ᴅᴏᴄᴜᴍᴇɴᴛs', callback_data=f'settings_#updatefilter-document-{filters_data["document"]}'),
       InlineKeyboardButton('✅' if filters_data['document'] else '❌', callback_data=f'settings#updatefilter-document-{filters_data["document"]}')
       ],[
       InlineKeyboardButton('🎞️ ᴠɪᴅᴇᴏs', callback_data=f'settings_#updatefilter-video-{filters_data["video"]}'),
       InlineKeyboardButton('✅' if filters_data['video'] else '❌', callback_data=f'settings#updatefilter-video-{filters_data["video"]}')
       ],[
       InlineKeyboardButton('📷 ᴘʜᴏᴛᴏs', callback_data=f'settings_#updatefilter-photo-{filters_data["photo"]}'),
       InlineKeyboardButton('✅' if filters_data['photo'] else '❌', callback_data=f'settings#updatefilter-photo-{filters_data["photo"]}')
       ],[
       InlineKeyboardButton('🎧 ᴀᴜᴅɪᴏs', callback_data=f'settings_#updatefilter-audio-{filters_data["audio"]}'),
       InlineKeyboardButton('✅' if filters_data['audio'] else '❌', callback_data=f'settings#updatefilter-audio-{filters_data["audio"]}')
       ],[
       InlineKeyboardButton('🎤 ᴠᴏɪᴄᴇs', callback_data=f'settings_#updatefilter-voice-{filters_data["voice"]}'),
       InlineKeyboardButton('✅' if filters_data['voice'] else '❌', callback_data=f'settings#updatefilter-voice-{filters_data["voice"]}')
       ],[
       InlineKeyboardButton('🎭 ᴀɴɪᴍᴀᴛɪᴏɴs', callback_data=f'settings_#updatefilter-animation-{filters_data["animation"]}'),
       InlineKeyboardButton('✅' if filters_data['animation'] else '❌', callback_data=f'settings#updatefilter-animation-{filters_data["animation"]}')
       ],[
       InlineKeyboardButton('🃏 sᴛɪᴄᴋᴇʀs', callback_data=f'settings_#updatefilter-sticker-{filters_data["sticker"]}'),
       InlineKeyboardButton('✅' if filters_data['sticker'] else '❌', callback_data=f'settings#updatefilter-sticker-{filters_data["sticker"]}')
       ],[
       InlineKeyboardButton('▶️ sᴋɪᴘ ᴅᴜᴘʟɪᴄᴀᴛᴇ', callback_data=f'settings_#updatefilter-duplicate-{config_data["duplicate"]}'),
       InlineKeyboardButton('✅' if config_data['duplicate'] else '❌', callback_data=f'settings#updatefilter-duplicate-{config_data["duplicate"]}')
       ],[
       InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data="settings#main")
       ]]
  return InlineKeyboardMarkup(buttons) 

async def next_filters_buttons(user_id):
  config_data = await get_configs(user_id)
  filters_data = config_data['filters']
  buttons = [[
       InlineKeyboardButton('📊 ᴘᴏʟʟ', callback_data=f'settings_#updatefilter-poll-{filters_data["poll"]}'),
       InlineKeyboardButton('✅' if filters_data['poll'] else '❌', callback_data=f'settings#updatefilter-poll-{filters_data["poll"]}')
       ],[
       InlineKeyboardButton('🔒 sᴇᴄᴜʀᴇ ᴍᴇssᴀɢᴇs', callback_data=f'settings_#updatefilter-protect-{config_data["protect"]}'),
       InlineKeyboardButton('✅' if config_data['protect'] else '❌', callback_data=f'settings#updatefilter-protect-{config_data["protect"]}')
       ],[
       InlineKeyboardButton('🛑 sɪᴢᴇ ʟɪᴍɪᴛ', callback_data='settings#file_size')
       ],[
       InlineKeyboardButton('💾 ᴇxᴛᴇɴsɪᴏɴ', callback_data='settings#get_extension')
       ],[
       InlineKeyboardButton('♦️ ᴋᴇʏᴡᴏʀᴅ', callback_data='settings#get_keyword')
       ],[
       InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data="settings#main")
       ]]
  return InlineKeyboardMarkup(buttons) 
