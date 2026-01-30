import time as tm
from database import db 
from config import Config

# Global dictionary for session data (Engine Memory)
STATUS = {}

def parse_buttons(text):
    """
    Caption mein buttons add karne ke liye (Inline Buttons).
    Format: [Name | Link]
    """
    from pyrogram.types import InlineKeyboardButton
    markup = []
    if not text: return None
    for line in text.split('\n'):
        row = []
        for btn in line.split(','):
            if '|' in btn:
                name, url = btn.split('|')
                row.append(InlineKeyboardButton(name.strip(), url=url.strip()))
        markup.append(row)
    return markup if markup else None

class STS:
    def __init__(self, id):
        self.id = id
        self.data = STATUS
        
    def verify(self):
        """Check karta hai ki memory mein task exist karta hai ya nahi."""
        return self.id in self.data
    
    def store(self, From, to, skip, total):
        """
        Forwarding setup save karta hai.
        'to' ab ek string ya list ho sakti hai (Multi-Target Ready).
        """
        self.data[self.id] = {
            "FROM": From, 
            'TO': to, 
            'total_files': 0, 
            'skip': int(skip), 
            'fetched': 0, 
            'filtered': 0, 
            'deleted': 0, 
            'duplicate': 0, 
            'last_id': 0, 
            'total': total,   
            'start': tm.time()
        }
        return self
        
    def get(self, value=None, full=False):
        """Memory se data nikalne ke liye."""
        values = self.data.get(self.id)
        if not values: return None
        if not full:
           mapping = {'FROM': 'FROM', 'TO': 'TO', 'skip': 'skip', 'total': 'total'}
           return values.get(mapping.get(value, value))
           
        class DataObject:
            def __init__(self, d, id):
                for k, v in d.items():
                    setattr(self, k, v)
                self.id = id
        return DataObject(values, self.id)

    def add(self, key=None, value=1, time=False):
        """Progress bar aur counters update karne ke liye."""
        if self.id not in self.data: return
        if time:
            self.data[self.id]['start'] = tm.time()
            return
        if key in self.data[self.id]:
            self.data[self.id][key] += value
    
    async def get_data(self, user_id):
        """
        DATABASE + CONFIG + MEMORY ka merger.
        Engine ko jo bhi chahiye, sab yahan se milega.
        """
        bot_data = await db.get_bot(user_id)
        configs = await db.get_configs(user_id)
        
        # Duplicate detection scope (Target channel based)
        duplicate_data = configs.get('duplicate')
        
        # Keyword Mapper (Word replacement dictionary)
        word_map = configs.get('replace_words', {})
        
        # Custom Buttons parsing
        button = parse_buttons(configs.get('button', ''))
        
        return (
            bot_data, 
            configs.get('caption'), 
            configs.get('forward_tag'), 
            {
                'chat_id': self.get('FROM'), 
                'offset': self.get('skip'), 
                'filters': configs.get('filters', {}),
                'keywords': configs.get('keywords', []), 
                'replace_words': word_map, # [NEW] Keyword Mapper
                'extensions': configs.get('extension', []), 
                'skip_duplicate': duplicate_data,
                'thumbnail': configs.get('thumbnail') # [NEW] Thumbnail Path
            }, 
            configs.get('protect'), 
            button
        )
