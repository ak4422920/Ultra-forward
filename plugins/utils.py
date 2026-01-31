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

# =================== LIVE & BULK HELPERS =================== #

def apply_replacements(text, word_map):
    """Word replacement logic jo Live aur Bulk dono mein kaam aayegi."""
    if not text or not word_map:
        return text
    for old_word, new_word in word_map.items():
        # Case insensitive replacement ke liye regex bhi use kar sakte hain
        text = text.replace(old_word, new_word)
    return text

def format_caption(msg, template, word_map):
    """File details ke sath caption format karne ke liye."""
    original_caption = msg.caption if msg.caption else ""
    
    # 1. Pehle word replacement apply karein
    processed_caption = apply_replacements(original_caption, word_map)
    
    # 2. Agar template (custom caption) hai toh placeholder replace karein
    if template:
        file_obj = msg.document or msg.video or msg.audio or msg.animation
        file_name = getattr(file_obj, 'file_name', 'No Name')
        final_caption = template.format(
            filename=file_name,
            caption=processed_caption
        )
        return final_caption
    
    return processed_caption

# =================== SESSION TRACKER (STS) =================== #

class STS:
    def __init__(self, id):
        self.id = str(id)
        self.data = temp.DATA
        
    def verify(self):
        """Check karta hai ki task memory mein hai ya nahi."""
        return self.id in self.data
    
    def store(self, From, to, skip, total):
        """Forwarding setup save karta hai."""
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
        """Task memory se data nikalne ke liye."""
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

    def add(self, key=None, value=1):
        """Progress bar update karne ke liye."""
        if self.id in self.data and key in self.data[self.id]:
            self.data[self.id][key] += value
    
    async def get_data(self, user_id):
        """Engine (regix.py) ke liye full data fetcher."""
        bot_data = await db.get_bot(user_id)
        configs = await db.get_configs(user_id)
        
        word_map = configs.get('replace_words', {})
        button_text = configs.get('button', '')
        button = parse_buttons(button_text)
        targets = self.get('TO')
        
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
