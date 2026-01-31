import time
from os import environ 
from config import Config
import motor.motor_asyncio
from pymongo import MongoClient

async def mongodb_version():
    x = MongoClient(Config.DATABASE_URI)
    mongodb_version = x.server_info()['version']
    return mongodb_version

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.bot = self.db.bots
        self.col = self.db.users
        self.nfy = self.db.notify
        self.chl = self.db.channels 
        self.tasks = self.db.tasks  # Persistence for Auto-Resume
        # [NEW] Collection for Live Forwarding (Auto-Post)
        self.live = self.db.live_forward 
        
    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            configs = {}, 
            ban_status = dict(is_banned=False, ban_reason="")
        )

    async def add_user(self, id, name):
        if not await self.is_user_exist(id):
            user = self.new_user(id, name)
            await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id': int(id)})
        return bool(user)

    # --- CONFIGURATION ENGINE ---

    async def update_configs(self, id, configs):
        await self.col.update_one({'id': int(id)}, {'$set': {'configs': configs}})
         
    async def get_configs(self, id):
        default = {
            'caption': None, 
            'duplicate': True, 
            'forward_tag': False,
            'file_size': 0, 
            'size_limit': None, 
            'extension': [], 
            'keywords': [],  
            'protect': False, 
            'button': None,
            'db_uri': Config.DATABASE_URI, 
            'thumbnail': None,
            'thumb_limit': Config.THUMB_LIMIT, 
            'replace_words': {}, 
            'admin_backup': Config.AUTO_BACKUP_CHANNEL, 
            'targets': [], 
            'filters': {
               'poll': True, 'text': True, 'audio': True, 'voice': True,
               'video': True, 'photo': True, 'document': True,
               'animation': True, 'sticker': True
            }
        }
        user = await self.col.find_one({'id': int(id)})
        if user and 'configs' in user:
            config_data = default.copy()
            config_data.update(user['configs'])
            return config_data
        return default 

    # --- LIVE FORWARDING (AUTO-POST) LOGIC ---
    # Isse bot ko pata chalega ki naya message kahan bhejna hai.

    async def add_live_link(self, user_id, source_id, target_ids):
        """Source aur Target ko live link karne ke liye."""
        # target_ids string ya list ho sakti hai (1 -> 5 support)
        data = {
            "user_id": int(user_id),
            "source_id": int(source_id),
            "target_ids": target_ids, 
            "active": True,
            "created_at": time.time()
        }
        return await self.live.update_one(
            {"source_id": int(source_id)}, 
            {"$set": data}, 
            upsert=True
        )

    async def get_live_map(self, source_id):
        """Listener isse check karega har naye message par."""
        return await self.live.find_one({"source_id": int(source_id), "active": True})

    async def remove_live_link(self, source_id):
        """Live forwarding band karne ke liye."""
        return await self.live.delete_one({"source_id": int(source_id)})

    async def get_all_live_links(self, user_id):
        """User ko dikhane ke liye ki usne kitne auto-posts set kiye hain."""
        cursor = self.live.find({"user_id": int(user_id)})
        return [doc async for doc in cursor]

    # --- TASK PERSISTENCE (Bulk Auto-Resume) ---

    async def add_task(self, user_id, task_data):
        task_data.update({
            'user_id': int(user_id), 
            'status': 'running', 
            'updated_at': time.time()
        })
        await self.tasks.update_one({'user_id': int(user_id)}, {'$set': task_data}, upsert=True)

    async def get_task(self, user_id):
        return await self.tasks.find_one({'user_id': int(user_id), 'status': 'running'})

    async def update_task_status(self, user_id, last_msg_id):
        await self.tasks.update_one(
            {'user_id': int(user_id), 'status': 'running'},
            {'$set': {'last_processed_id': last_msg_id, 'updated_at': time.time()}}
        )

    async def get_active_tasks(self):
        return self.tasks.find({'status': 'running'})

    async def remove_task(self, user_id):
        await self.tasks.delete_one({'user_id': int(user_id)})

    # --- DUPLICATE FINGERPRINT ---

    async def is_duplicate(self, chat_id, file_unique_id):
        collection = self.db[f"duplicates_{abs(chat_id)}"]
        result = await collection.find_one({'file_unique_id': file_unique_id})
        return bool(result)

    async def save_fingerprint(self, chat_id, file_unique_id):
        collection = self.db[f"duplicates_{abs(chat_id)}"]
        await collection.update_one(
            {'file_unique_id': file_unique_id},
            {'$set': {'file_unique_id': file_unique_id, 'timestamp': time.time()}},
            upsert=True
        )

    # --- BOT & WORKER MANAGEMENT ---

    async def add_bot(self, datas):
       if not await self.is_bot_exist(datas['user_id']):
          await self.bot.insert_one(datas)
          
    async def remove_bot(self, user_id):
       await self.bot.delete_many({'user_id': int(user_id)})
      
    async def get_bot(self, user_id: int):
       return await self.bot.find_one({'user_id': user_id})
                                          
    async def is_bot_exist(self, user_id):
       bot = await self.bot.find_one({'user_id': user_id})
       return bool(bot)

    async def total_users_bots_count(self):
        bcount = await self.bot.count_documents({})
        count = await self.col.count_documents({})
        return count, bcount

    # --- BAN SYSTEM ---
    
    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(is_banned=True, ban_reason=ban_reason)
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(is_banned=False, ban_reason='')
        user = await self.col.find_one({'id': int(id)})
        if not user: return default
        return user.get('ban_status', default)

db = Database(Config.DATABASE_URI, Config.DATABASE_NAME)
