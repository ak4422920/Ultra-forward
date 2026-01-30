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
        
    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            configs = {}, # Initialize empty configs
            ban_status = dict(is_banned=False, ban_reason="")
        )

    async def add_user(self, id, name):
        if not await self.is_user_exist(id):
            user = self.new_user(id, name)
            await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id': int(id)})
        return bool(user)

    # --- CONFIGURATION ENGINE (Synced with Feature List) ---

    async def update_configs(self, id, configs):
        await self.col.update_one({'id': int(id)}, {'$set': {'configs': configs}})
         
    async def get_configs(self, id):
        """
        Saare features ke defaults yahan hain:
        Multi-target, Keyword Mapper, Dynamic Thumbnail Limit, etc.
        """
        default = {
            'caption': None, 
            'duplicate': True, 
            'forward_tag': False,
            'file_size': 0, 
            'size_limit': None, 
            'extension': [], # List for multiple extensions
            'keywords': [],  # List for allowed keywords
            'protect': False, 
            'button': None,
            'db_uri': Config.DATABASE_URI, 
            'thumbnail': None,
            'thumb_limit': Config.THUMB_LIMIT, # Dynamic VPS limit
            'replace_words': {}, # Keyword Mapper
            'admin_backup': Config.AUTO_BACKUP_CHANNEL, # Hidden Auto Backup
            'targets': [], # Multi-destination support (1 -> 5)
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

    # --- TASK PERSISTENCE (Auto-Resume Logic) ---

    async def add_task(self, user_id, task_data):
        """Task ko DB mein save karna taaki restart par resume ho sake."""
        task_data.update({
            'user_id': int(user_id), 
            'status': 'running', 
            'updated_at': time.time()
        })
        await self.tasks.update_one({'user_id': int(user_id)}, {'$set': task_data}, upsert=True)

    async def get_task(self, user_id):
        return await self.tasks.find_one({'user_id': int(user_id), 'status': 'running'})

    async def update_task_status(self, user_id, last_msg_id):
        """Current progress save karna (Fetched ID)."""
        await self.tasks.update_one(
            {'user_id': int(user_id), 'status': 'running'},
            {'$set': {'last_processed_id': last_msg_id, 'updated_at': time.time()}}
        )

    async def get_active_tasks(self):
        """Bot start hote hi active tasks uthane ke liye."""
        return self.tasks.find({'status': 'running'})

    async def remove_task(self, user_id):
        await self.tasks.delete_one({'user_id': int(user_id)})

    # --- DUPLICATE FINGERPRINT (Unequify Logic) ---

    async def is_duplicate(self, chat_id, file_unique_id):
        """Check if file was already sent to this channel."""
        collection = self.db[f"duplicates_{abs(chat_id)}"]
        result = await collection.find_one({'file_unique_id': file_unique_id})
        return bool(result)

    async def save_fingerprint(self, chat_id, file_unique_id):
        """Save file record to prevent duplicates."""
        collection = self.db[f"duplicates_{abs(chat_id)}"]
        await collection.update_one(
            {'file_unique_id': file_unique_id},
            {'$set': {'file_unique_id': file_unique_id, 'timestamp': time.time()}},
            upsert=True
        )

    # --- BOT & CHANNEL MANAGEMENT ---

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
                                          
    async def get_user_channels(self, user_id: int):
       channels = self.chl.find({"user_id": int(user_id)})
       return [channel async for channel in channels]

    async def total_users_bots_count(self):
        bcount = await self.bot.count_documents({})
        count = await self.col.count_documents({})
        return count, bcount

    # --- BAN & NOTIFY SYSTEM ---
    
    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(is_banned=True, ban_reason=ban_reason)
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(is_banned=False, ban_reason='')
        user = await self.col.find_one({'id': int(id)})
        if not user: return default
        return user.get('ban_status', default)

db = Database(Config.DATABASE_URI, Config.DATABASE_NAME)
