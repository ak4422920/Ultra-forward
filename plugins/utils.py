import time as tm
from database import db 
from .test import parse_buttons

STATUS = {}

class STS:
    def __init__(self, id):
        self.id = id
        self.data = STATUS
    
    def set(self, key, value):
        if self.id not in self.data:
            self.data[self.id] = {}
        self.data[self.id][key] = value
        
    def verify(self):
        return self.data.get(self.id)
    
    def store(self, From, to, skip, limit):
        self.data[self.id] = {
            "FROM": From, 
            'TO': to, 
            'total_files': 0, 
            'skip': skip, 
            'limit': limit,
            'fetched': skip, 
            'filtered': 0, 
            'deleted': 0, 
            'duplicate': 0, 
            'total': limit, 
            'start': 0
        }
        self.get(full=True)
        return STS(self.id)
        
    def get(self, value=None, full=False):
        values = self.data.get(self.id)
        if not values: 
            return None
        if not full:
           return values.get(value)
        for k, v in values.items():
            setattr(self, k, v)
        return self

    def add(self, key=None, value=1, time=False):
        if self.id not in self.data:
            self.data[self.id] = {}
            
        if time:
          return self.data[self.id].update({'start': tm.time()})
        
        current_val = self.get(key)
        if current_val is None:
            current_val = 0
            
        self.data[self.id].update({key: current_val + value}) 
    
    def divide(self, no, by):
       by = 1 if int(by) == 0 else by 
       return int(no) / by 
    
    async def get_data(self, user_id):
        # [FIX] Load attributes (TO, FROM, etc.) before accessing them
        self.get(full=True) 
        
        bot = await db.get_bot(user_id)
        k, filters = self, await db.get_filters(user_id)
        size, configs = None, await db.get_configs(user_id)
        
        if configs['duplicate']:
           # Now self.TO exists because we called self.get(full=True) above
           duplicate = [configs['db_uri'], self.TO]
        else:
           duplicate = False
           
        button = parse_buttons(configs['button'] if configs['button'] else '')
        if configs['file_size'] != 0:
            size = [configs['file_size'], configs['size_limit']]
            
        return bot, configs['caption'], configs['forward_tag'], {
            'chat_id': k.FROM, 
            'limit': k.limit, 
            'offset': k.skip, 
            'filters': filters,
            'keywords': configs['keywords'], 
            'button': button, 
            'duplicate': duplicate, 
            'protect': configs['protect'], 
            'extension': configs['extension'], 
            'size': size,
            'replace_text': configs.get('replace_text'),
            'remove_text': configs.get('remove_text'),
            'thumbnail': configs.get('thumbnail'),
            'thumb_toggle': configs.get('thumb_toggle'),
            'workers': configs.get('workers', 1)
        }
