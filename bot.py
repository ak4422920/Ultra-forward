import asyncio
import logging 
import logging.config
from database import db 
from config import Config, temp
from pyrogram import Client, __version__
from pyrogram.raw.all import layer 
from pyrogram.enums import ParseMode
from aiohttp import web
from plugins import web_server 

# Regix plugin se engine import karna (Auto-Resume ke liye)
try:
    from plugins.regix import auto_restart_task
except ImportError:
    # Agar abhi regix tayaar nahi hai toh ye error nahi dega
    auto_restart_task = None

# Logging Setup (Using our fine-tuned logging.conf)
logging.config.fileConfig('logging.conf')
log = logging.getLogger("Bot")

class Bot(Client): 
    def __init__(self):
        super().__init__(
            name=Config.BOT_SESSION,
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            bot_token=Config.BOT_TOKEN,   
            sleep_threshold=10,
            workers=200, # High workers for 1->5 target speed
            plugins={"root": "plugins"}
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.DEFAULT)
        
        log.info(f"🚀 {me.first_name} (Elite V3) started on @{me.username}")

        # --- Web Server (Keep-Alive for Koyeb/VPS) ---
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            await web.TCPSite(app, "0.0.0.0", Config.PORT).start()
            log.info(f"🌐 Web Server active on Port: {Config.PORT}")
        except Exception as e:
            log.warning(f"🌐 Web Server Warning: {e}")

        # ================= AUTO-RESUME ENGINE ================= #
        # Bot start hote hi database check karega
        if auto_restart_task:
            log.info("🔍 Scanning Database for interrupted tasks...")
            try:
                active_tasks = await db.get_active_tasks()
                task_count = 0
                
                async for task in active_tasks:
                    user_id = task['user_id']
                    task_count += 1
                    
                    # Background mein task restart karna
                    asyncio.create_task(auto_restart_task(self, user_id, task))
                    
                    # User ko silent notification
                    try:
                        await self.send_message(
                            chat_id=user_id, 
                            text="<b>♻️ ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ\nAapka forwarding task automatically resume ho gaya hai!</b>"
                        )
                    except:
                        pass
                
                if task_count > 0:
                    log.info(f"✅ Successfully resumed {task_count} active tasks.")
                else:
                    log.info("ℹ️ No active tasks found to resume.")

            except Exception as e:
                log.error(f"❌ Auto-Resume Logic Error: {e}")
        else:
            log.error("❌ 'auto_restart_task' not found in regix.py!")

    async def stop(self, *args):
        await super().stop()
        log.info(f"@{self.username} is shutting down... Bye! 👋")

if __name__ == "__main__":
    Bot().run()
