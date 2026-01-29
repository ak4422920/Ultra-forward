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

# Automatic restart logic ko handle karne ke liye function import (Ye hum regix.py mein banayenge)
from plugins.regix import auto_restart_task

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
        logging.info(f"{me.first_name} (Layer {layer}) started on @{me.username}.")
        
        # Web server initialization
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, Config.PORT).start()
        
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.DEFAULT)
        
        logging.info("Checking for unfinished tasks to Auto-Resume...")

        # ================= FULLY AUTOMATIC RESUME LOGIC ================= #
        # Database se un tasks ko uthana jinka status 'running' hai
        active_tasks = await db.get_active_tasks()
        
        async for task in active_tasks:
            user_id = task['user_id']
            logging.info(f"Automatically restarting task for User: {user_id}")
            
            # Har task ko background mein alag se start karna taaki bot hang na ho
            asyncio.create_task(auto_restart_task(self, user_id, task))
            
            # User ko update dena (Optional)
            try:
                await self.send_message(
                    chat_id=user_id, 
                    text="<b>♻️ ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ: Aapka forwarding task automatically resume ho gaya hai!</b>"
                )
            except:
                pass

        logging.info("All pending tasks have been resumed automatically.")

    async def stop(self, *args):
        msg = f"@{self.username} stopped. Bye."
        await super().stop()
        logging.info(msg)

app = Bot()
app.run()
