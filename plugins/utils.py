import time as tm
from database import db 
from .test import parse_buttons

STATUS = {}

class STS:
    def __init__(self, id):
        self.id = id
        self.data = STATUS
        
    def verify(self):
        """Task ID valid hai ya nahi check karne ke liye."""
        return self.data.get(self.id)
    
    def store(self, From, to, skip, limit):
        """Task start hote waqt initial data save karta hai."""
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
        """Data fetch karne ke liye."""
        values = self.data.get(self.id)
        if not values:
            return None
        if not full:
           return values.get(value)
        for k, v in values.items():
            setattr(self, k, v)
        return self

    def add(self, key=None, value=1, time=False):
        """Counters (fetched/files) ya start time update karne ke liye."""
        if self.id not in self.data:
            return
        if time:
          return self.data[self.id].update({'start': tm.time()})
        current_val = self.data[self.id].get(key, 0)
        self.data[self.id].update({key: current_val + value}) 
    
    def divide(self, no, by):
       """ETA aur Speed calculation ke liye math helper."""
       by = 1 if int(by) == 0 else by 
       return int(no) / by 
    
    async def get_data(self, user_id):
        """Database se bot aur user settings fetch karta hai."""
        bot = await db.get_bot(user_id)
        configs = await db.get_configs(user_id)
        filters = await db.get_filters(user_id)
        
        # Duplicate detection setup
        duplicate = [configs['db_uri'], self.get('TO')] if configs['duplicate'] else False
        
        # Inline buttons parse karna
        button = parse_buttons(configs['button'] if configs['button'] else '')
        
        # File size limit check
        size = [configs['file_size'], configs['size_limit']] if configs['file_size'] != 0 else None
        
        return (
            bot, 
            configs['caption'], 
            configs['forward_tag'], 
            {
                'chat_id': self.get('FROM'), 
                'limit': self.get('limit'), 
                'offset': self.get('skip'), 
                'filters': filters,
                'keywords': configs['keywords'], 
                'media_size': size, 
                'extensions': configs['extension'], 
                'skip_duplicate': duplicate
            }, 
            configs['protect'], 
            button
        )
