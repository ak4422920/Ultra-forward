import time as tm
from database import db 
from .test import parse_buttons

# Global dictionary for session data
STATUS = {}

class STS:
    def __init__(self, id):
        self.id = id
        self.data = STATUS
        
    def verify(self):
        """Task ID valid hai ya nahi check karne ke liye."""
        return self.id in self.data
    
    def store(self, From, to, skip, total, limit=0):
        """
        Setup ke details save karta hai. 
        Note: total yahan 'last_msg_id' hai jo regix use karta hai.
        """
        self.data[self.id] = {
            "FROM": From, 
            'TO': to, 
            'total_files': 0, 
            'skip': skip, 
            'limit': limit,
            'fetched': 0, # Kitne messages check kiye
            'filtered': 0, 
            'deleted': 0, 
            'duplicate': 0, 
            'last_id': total, # Source channel ka aakhri message ID
            'total': total,   # UI mein dikhane ke liye total messages
            'start': tm.time()
        }
        return self
        
    def get(self, value=None, full=False):
        """Data fetch karne ke liye."""
        values = self.data.get(self.id)
        if not values:
            return None
        if not full:
           # Mapping for backward compatibility with regix.py
           mapping = {'FROM': 'FROM', 'TO': 'TO', 'skip': 'skip', 'limit': 'limit', 'total': 'total'}
           return values.get(mapping.get(value, value))
           
        # Object format mein return karna for i.total, i.fetched etc.
        class DataObject:
            def __init__(self, d, id):
                for k, v in d.items():
                    setattr(self, k, v)
                self.id = id
        return DataObject(values, self.id)

    def add(self, key=None, value=1, time=False):
        """Counters update karne ke liye."""
        if self.id not in self.data:
            return
        if time:
            self.data[self.id]['start'] = tm.time()
            return
        if key in self.data[self.id]:
            self.data[self.id][key] += value
    
    def divide(self, no, by):
       """ETA calculation helper."""
       by = 1 if int(by) == 0 else by 
       return float(no) / by 
    
    async def get_data(self, user_id):
        """Database se settings fetch karna."""
        bot = await db.get_bot(user_id)
        configs = await db.get_configs(user_id)
        filters = await db.get_filters(user_id)
        
        # Duplicate detection setup
        duplicate = [configs['db_uri'], self.get('TO')] if configs.get('duplicate') else False
        
        # Inline buttons parse karna
        button = parse_buttons(configs.get('button', ''))
        
        # File size limit check
        size = [configs.get('file_size', 0), configs.get('size_limit')] if configs.get('file_size') != 0 else None
        
        return (
            bot, 
            configs.get('caption'), 
            configs.get('forward_tag'), 
            {
                'chat_id': self.get('FROM'), 
                'limit': self.get('limit'), 
                'offset': self.get('skip'), 
                'filters': filters,
                'keywords': configs.get('keywords'), 
                'media_size': size, 
                'extensions': configs.get('extension'), 
                'skip_duplicate': duplicate
            }, 
            configs.get('protect'), 
            button
        )
