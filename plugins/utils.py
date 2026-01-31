import time as tm
from database import db 
from config import Config, temp

# =================== BUTTON PARSER =================== #

def parse_buttons(text):
    """
    Caption mein custom inline buttons add karne ke liye.
    Format: [Name | Link] - Comma separated for rows.
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

# =================== SESSION TRACKER (STS) =================== #

class STS:
    def __init__(self, id):
        self.id = str(id)
        # Hum config.py ka global storage use karenge
        self.data = temp.DATA
        
    def verify(self):
        """Check karta hai ki task memory mein hai ya nahi."""
        return self.id in self.data
    
    def store(self, From, to, skip, total):
        """
        Forwarding setup save karta hai.
        'to' ab ek multi-target string/list support karta hai.
        """
        self.data[self.id] = {
            "FROM": From, 
            'TO': to, 
            'total_files': 0, 
            'skip': int(skip), 
            'fetched': 0, 
            'duplicate': 0, 
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
           
        # Full object return for stats mapping
        class DataObject:
            def __init__(self, d, id):
                for k, v in d.items():
                    setattr(self, k, v)
                self.id = id
        return DataObject(values, self.id)

    def add(self, key=None, value=1):
        """Progress bar aur counters (stats) update karne ke liye."""
        if self.id in self.data and key in self.data[self.id]:
            self.data[self.id][key] += value
    
    async def get_data(self, user_id):
        """
        Engine (regix.py) ko jo bhi details chahiye, sab yahan se merge hokar jati hain.
        """
        bot_data = await db.get_bot(user_id)
        configs = await db.get_configs(user_id)
        
        # Word Replacement logic
        word_map = configs.get('replace_words', {})
        
        # Custom Buttons logic
        button_text = configs.get('button', '')
        button = parse_buttons(button_text)
        
        # Target list extraction
        targets = self.get('TO')
        
        # Ye tuple exactly regix.py ke core_forward_engine se match karta hai
        return (
            bot_data, 
            configs.get('caption'), 
            configs.get('forward_tag'), 
            {
                'chat_id': self.get('FROM'), 
                'offset': self.get('skip'), 
                'replace_words': word_map, 
                'thumbnail': configs.get('thumbnail'),
                'targets': targets 
            }, 
            configs.get('protect'), 
            button
        )
