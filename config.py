import datetime
from os import environ 

class Config:
    API_ID = int(environ.get("API_ID", "2554744")) # Aapka API ID
    API_HASH = environ.get("API_HASH", "87545xxxx") # Aapka API HASH
    BOT_TOKEN = environ.get("BOT_TOKEN", "") 
    BOT_SESSION = environ.get("BOT_SESSION", "AutoXXPostBot") 
    
    # Database Variable matching database.py
    DATABASE_URI = environ.get("DATABASE_URI", environ.get("DATABASE", "")) 
    DATABASE_NAME = environ.get("DATABASE_NAME", "Cluster0")
    
    BOT_OWNER_ID = [int(id) for id in environ.get("BOT_OWNER_ID", '5482682830').split()]
    LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002416220645'))
    
    # Backup Channel Feature
    ADMIN_BACKUP_CHANNEL = int(environ.get('ADMIN_BACKUP_CHANNEL', '-1003456547251')) 
    
    FORCE_SUB_CHANNEL = environ.get("FORCE_SUB_CHANNEL", "https://t.me/AkmovieVerse") 
    FORCE_SUB_ON = environ.get("FORCE_SUB_ON", "True")
    PORT = environ.get('PORT', '8080')

class temp(object): 
    lock = {}           # Task locking
    CANCEL = {}         # Task cancellation
    DATA = {}           # Task memory storage (Bhot zaroori hai!)
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []   # Active chat tracking
