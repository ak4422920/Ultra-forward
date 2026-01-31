import asyncio
import logging 
import logging.config
from database import db 
from config import Config, temp
from pyrogram import Client, filters, __version__
from pyrogram.raw.all import layer 
from pyrogram.enums import ParseMode
from aiohttp import web
from plugins import web_server 

# Imports for Caption & Word Mapping (Live Forwarding ke liye)
import re

# Regix plugin se engine import karna (Auto-Resume ke liye)
try:
    from plugins.regix import auto_restart_task
except ImportError:
    auto_restart_task = None

# Logging Setup
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
            workers=200, 
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

        # --- Web Server ---
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            await web.TCPSite(app, "0.0.0.0", Config.PORT).start()
            log.info(f"🌐 Web Server active on Port: {Config.PORT}")
        except Exception as e:
            log.warning(f"🌐 Web Server Warning: {e}")

        # ================= AUTO-RESUME ENGINE ================= #
        if auto_restart_task:
            log.info("🔍 Scanning Database for interrupted tasks...")
            try:
                active_tasks = await db.get_active_tasks()
                async for task in active_tasks:
                    user_id = task['user_id']
                    asyncio.create_task(auto_restart_task(self, user_id, task))
                    log.info(f"✅ Resumed task for User: {user_id}")
            except Exception as e:
                log.error(f"❌ Auto-Resume Logic Error: {e}")

    # ================= LIVE FORWARDING LISTENER ================= #
    # Ye part har naye message ko monitor karega
    @Client.on_message(filters.chat & ~filters.private)
    async def live_forwarder(self, message):
        source_id = message.chat.id
        
        # 1. Check karein kya ye channel live mapping mein hai?
        mapping = await db.get_live_map(source_id)
        if not mapping:
            return

        user_id = mapping['user_id']
        target_ids = str(mapping['target_ids']).split(",")
        
        # 2. User ki configurations uthana (Caption, Filters, etc.)
        configs = await db.get_configs(user_id)
        
        # 3. Message Type Filter (Agar user ne koi media band kiya ho)
        msg_type = message.media.value if message.media else "text"
        if not configs['filters'].get(msg_type, True):
            return

        # 4. Process Caption & Word Replacement
        new_caption = message.caption or ""
        word_map = configs.get('replace_words', {})
        for old_w, new_w in word_map.items():
            new_caption = new_caption.replace(old_w, new_w)
        
        if configs.get('caption'):
            # Agar user ne global custom caption set kiya hai
            new_caption = configs['caption'].format(
                filename=getattr(message.document or message.video, 'file_name', 'None'),
                caption=new_caption
            )

        # 5. Delivery to Targets
        for target in target_ids:
            try:
                t_id = int(target.strip())
                # Copy message (instantly)
                await message.copy(
                    chat_id=t_id,
                    caption=new_caption,
                    parse_mode=ParseMode.HTML,
                    protect_content=configs.get('protect', False)
                )
            except Exception as e:
                log.error(f"Live Forwarding Failed for {t_id}: {e}")

    async def stop(self, *args):
        await super().stop()
        log.info(f"@{self.username} is shutting down... Bye! 👋")

if __name__ == "__main__":
    Bot().run()
