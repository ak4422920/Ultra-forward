import time as tm
from database import db 
from config import Config

# Global dictionary for session data (Engine Memory)
STATUS = {}

def parse_buttons(text):
    """
    Caption mein custom inline buttons add karne ke liye.
    Format: [Name | Link]
    """
    from pyrogram.types import InlineKeyboardButton
    markup = []
    if not text: return None
    try:
        for line in text.split('\n'):
            row = []
            for btn in line.split(','):
                if '|' in btn:
                    name, url = btn.split('|')
                    row.append(InlineKeyboardButton(name.strip(), url=url.strip()))
            if row: markup.append(row)
    except Exception: pass
    return markup if markup else None

class STS:
    def __init__(self, id):
        self.id = id
        self.data = STATUS
        
    def verify(self):
        """Check karta hai ki task memory mein hai ya expired ho gaya."""
        return self.id in self.data
    
    def store(self, From, to, skip, total):
        """
        Forwarding setup save karta hai.
        'to' ab ek multi-target string hai.
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
        """Task memory se specifically data nikalne ke liye."""
        values = self.data.get(self.id)
        if not values: return None
        if not full:
           return values.get(value)
           
        class DataObject:
            def __init__(self, d, id):
                for k, v in d.items():
                    setattr(self, k, v)
                self.id = id
        return DataObject(values, self.id)

    def add(self, key=None, value=1, time=False):
        """Progress bar aur counters (stats) update karne ke liye."""
        if self.id not in self.data: return
        if time:
            self.data[self.id]['start'] = tm.time()
            return
        if key in self.data[self.id]:
            self.data[self.id][key] += value
    
    async def get_data(self, user_id):
        """
        DATABASE + CONFIG + MEMORY ka merger.
        Engine (regix.py) ko jo bhi asala-barood chahiye, sab yahan se milega.
        """
        bot_data = await db.get_bot(user_id)
        configs = await db.get_configs(user_id)
        
        # Word Replacement logic (Keyword Mapper)
        word_map = configs.get('replace_words', {})
        
        # Custom Buttons logic
        button_text = configs.get('button', '')
        button = parse_buttons(button_text)
        
        # Target list extraction (From saved targets or manual input)
        targets = self.get('TO')
        
        return (
            bot_data, 
            configs.get('caption'), 
            configs.get('forward_tag'), 
            {
                'chat_id': self.get('FROM'), 
                'offset': self.get('skip'), 
                'filters': configs.get('filters', {}),
                'keywords': configs.get('keywords', []), 
                'replace_words': word_map, 
                'extensions': configs.get('extension', []), 
                'skip_duplicate': configs.get('duplicate'),
                'thumbnail': configs.get('thumbnail'),
                'targets': targets # [NEW] Integrated for engine routing
            }, 
            configs.get('protect'), 
            button
        )
