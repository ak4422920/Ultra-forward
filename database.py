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
        self.tasks = self.db.tasks  # Task queue for Auto-Resume
        
    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
        )

    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_bots_count(self):
        bcount = await self.bot.count_documents({})
        count = await self.col.count_documents({})
        return count, bcount

    async def total_channels(self):
        count = await self.chl.count_documents({})
        return count
    
    async def remove_ban(self, id):
        ban_status = dict(is_banned=False, ban_reason='')
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})
    
    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(is_banned=True, ban_reason=ban_reason)
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(is_banned=False, ban_reason='')
        user = await self.col.find_one({'id':int(id)})
        if not user: return default
        return user.get('ban_status', default)

    async def get_all_users(self):
        return self.col.find({})
    
    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})
 
    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        b_users = [user['id'] async for user in users]
        return b_users

    async def update_configs(self, id, configs):
        await self.col.update_one({'id': int(id)}, {'$set': {'configs': configs}})
         
    async def get_configs(self, id):
        """Merge Logic: Purane users ka data naye defaults ke saath merge."""
        default = {
            'caption': None, 'duplicate': True, 'forward_tag': False,
            'file_size': 0, 'size_limit': None, 'extension': None,
            'keywords': None, 'protect': None, 'button': None,
            'db_uri': Config.DATABASE_URI, 'thumbnail': None,
            'replace_words': {}, 'admin_backup': None,
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
       
    async def add_bot(self, datas):
       if not await self.is_bot_exist(datas['user_id']):
          await self.bot.insert_one(datas)
          
    async def remove_bot(self, user_id):
       await self.bot.delete_many({'user_id': int(user_id)})
      
    async def get_bot(self, user_id: int):
       bot = await self.bot.find_one({'user_id': user_id})
       return bot if bot else None
                                          
    async def is_bot_exist(self, user_id):
       bot = await self.bot.find_one({'user_id': user_id})
       return bool(bot)
                                          
    async def in_channel(self, user_id: int, chat_id: int) -> bool:
       channel = await self.chl.find_one({"user_id": int(user_id), "chat_id": int(chat_id)})
       return bool(channel)
    
    async def add_channel(self, user_id: int, chat_id: int, title, username):
       channel = await self.in_channel(user_id, chat_id)
       if channel: return False
       return await self.chl.insert_one({"user_id": user_id, "chat_id": chat_id, "title": title, "username": username})
    
    async def remove_channel(self, user_id: int, chat_id: int):
       channel = await self.in_channel(user_id, chat_id )
       if not channel: return False
       return await self.chl.delete_many({"user_id": int(user_id), "chat_id": int(chat_id)})
    
    async def get_channel_details(self, user_id: int, chat_id: int):
       return await self.chl.find_one({"user_id": int(user_id), "chat_id": int(chat_id)})
       
    async def get_user_channels(self, user_id: int):
       channels = self.chl.find({"user_id": int(user_id)})
       return [channel async for channel in channels]
     
    async def get_filters(self, user_id):
       filters = []
       configs = await self.get_configs(user_id)
       filter_data = configs.get('filters', {})
       for k, v in filter_data.items():
          if v == False: filters.append(str(k))
       return filters
              
    async def add_frwd(self, user_id):
       return await self.nfy.insert_one({'user_id': int(user_id)})
    
    async def rmve_frwd(self, user_id=0, all=False):
       data = {} if all else {'user_id': int(user_id)}
       return await self.nfy.delete_many(data)
    
    async def get_all_frwd(self):
       return self.nfy.find({})

    # --- Task Persistence (For Auto-Resume) ---
    async def add_task(self, user_id, task_data):
        task_data.update({'user_id': int(user_id), 'status': 'running'})
        await self.tasks.update_one({'user_id': int(user_id)}, {'$set': task_data}, upsert=True)

    async def get_task(self, user_id):
        return await self.tasks.find_one({'user_id': int(user_id), 'status': 'running'})

    async def update_task_status(self, user_id, last_msg_id):
        await self.tasks.update_one(
            {'user_id': int(user_id), 'status': 'running'},
            {'$set': {'last_processed_id': last_msg_id}}
        )

    async def get_active_tasks(self):
        return self.tasks.find({'status': 'running'})

    async def remove_task(self, user_id):
        await self.tasks.delete_one({'user_id': int(user_id)})

    # ================= DUPLICATE FINGERPRINT LOGIC ================= #
    #
    async def is_duplicate(self, db_uri, chat_id, file_unique_id):
        """Check if file fingerprint exists for this specific channel."""
        collection = self.db[f"duplicates_{chat_id}"]
        result = await collection.find_one({'file_unique_id': file_unique_id})
        return bool(result)

    async def save_fingerprint(self, db_uri, chat_id, file_unique_id):
        """Save file fingerprint to isolation collection."""
        collection = self.db[f"duplicates_{chat_id}"]
        await collection.update_one(
            {'file_unique_id': file_unique_id},
            {'$set': {'file_unique_id': file_unique_id, 'timestamp': time.time()}},
            upsert=True
        )
    
db = Database(Config.DATABASE_URI, Config.DATABASE_NAME)
