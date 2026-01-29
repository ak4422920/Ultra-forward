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

# Regix plugin se auto-resume function import karna
from plugins.regix import auto_restart_task

# Logging Setup
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class Bot(Client): 
    def __init__(self):
        super().__init__(
            name=Config.BOT_SESSION,
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
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.DEFAULT)
        
        logging.info(f"🚀 {me.first_name} (Layer {layer}) started on @{me.username}")

        # --- Web Server Setup ---
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            bind_address = "0.0.0.0"
            await web.TCPSite(app, bind_address, Config.PORT).start()
            logging.info(f"🌐 Web Server started on Port: {Config.PORT}")
        except Exception as e:
            logging.error(f"❌ Web Server Error: {e}")

        # ================= FULLY AUTOMATIC RESUME LOGIC ================= #
        logging.info("🔍 Checking Database for unfinished tasks...")
        
        try:
            active_tasks = await db.get_active_tasks()
            task_count = 0
            
            async for task in active_tasks:
                user_id = task['user_id']
                task_count += 1
                
                # Background mein task start karna (Asynchronous)
                asyncio.create_task(auto_restart_task(self, user_id, task))
                
                # User ko notification bhejna (Silent Failure agar bot blocked hai)
                try:
                    await self.send_message(
                        chat_id=user_id, 
                        text="<b>♻️ ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ: Aapka forwarding task automatically resume ho gaya hai!</b>"
                    )
                except:
                    pass
            
            if task_count > 0:
                logging.info(f"✅ Successfully resumed {task_count} active tasks.")
            else:
                logging.info("ℹ️ No active tasks found to resume.")

        except Exception as e:
            logging.error(f"❌ Auto-Resume Logic Error: {e}")

    async def stop(self, *args):
        await super().stop()
        logging.info(f"@{self.username} stopped. Bye! 👋")

if __name__ == "__main__":
    app = Bot()
    app.run()
