import asyncio
import logging 
import logging.config
from database import db 
from config import Config, temp  
from pyrogram import Client, __version__
from pyrogram.raw.all import layer 
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait 
from aiohttp import web
from plugins import web_server 

logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class Bot(Client): 
    def __init__(self):
        super().__init__(
            Config.BOT_SESSION,
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            bot_token=Config.BOT_TOKEN,   
            sleep_threshold=10,
            workers=200,
            plugins={"root": "plugins"}
        )
        self.log = logging

    async def start(self):
        await super().start()
        me = await self.get_me()
        logging.info(f"{me.first_name} with for pyrogram v{__version__} (Layer {layer}) started on @{me.username}.")
        
        # Web Server Initialization
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, Config.PORT).start()
        
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.DEFAULT)
        
        # --- [NEW] FEATURE 1: INITIALIZE LIVE FORWARDING ---
        logging.info("Loading Live Forwarding tasks from Database...")
        live_tasks = await db.get_live_tasks()
        async for task in live_tasks:
            source = task['source']
            if source not in temp.LIVE_TASKS:
                temp.LIVE_TASKS[source] = []
            temp.LIVE_TASKS[source].append({
                'user_id': task['user_id'],
                'targets': task['targets']
            })
        
        # --- [UPDATE] FEATURE 3: AUTO-RESUME LOGIC ---
        text = "<b>๏[-ิ_•ิ]๏ ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ !</b>"
        logging.info("Checking for interrupted forwarding tasks...")
        success = failed = 0
        users = await db.get_all_frwd()
        
        async for user in users:
           chat_id = user['user_id']
           try:
              # Restart message notification
              await self.send_message(chat_id, text)
              
              # Agar task data present hai, toh usey Auto-Resume state mein load karein
              if 'from_chat' in user and 'to_chat' in user:
                  logging.info(f"Task found for user {chat_id}. Preparing for Auto-Resume...")
                  temp.RESUME_TASKS[chat_id] = user
              
              success += 1
           except FloodWait as e:
              await asyncio.sleep(e.value + 1)
              await self.send_message(chat_id, text)
              success += 1
           except Exception:
              failed += 1 
              
        if (success + failed) != 0:
           # Task notification table clear karein (As per original logic)
           await db.rmve_frwd(all=True)
           logging.info(f"Restart status - Success: {success}, Failed: {failed}")
        
        logging.info("Bot is fully operational and tasks are synchronized.")

    async def stop(self, *args):
        msg = f"@{self.username} stopped. Bye."
        await super().stop()
        logging.info(msg)

app = Bot()
app.run()
