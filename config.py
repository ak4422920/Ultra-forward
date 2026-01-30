import datetime
from os import environ 

class Config:
    # --- BASIC BOT SETTINGS ---
    API_ID = int(environ.get("API_ID", ""))
    API_HASH = environ.get("API_HASH", "")
    BOT_TOKEN = environ.get("BOT_TOKEN", "") 
    BOT_SESSION = environ.get("BOT_SESSION", "AutoForwarder_V3") 
    
    # --- DATABASE SETTINGS ---
    DATABASE_URI = environ.get("DATABASE_URI", environ.get("DATABASE", "")) 
    DATABASE_NAME = environ.get("DATABASE_NAME", "Cluster0")
    
    # --- ADMIN & LOGGING ---
    BOT_OWNER_ID = [int(id) for id in environ.get("BOT_OWNER_ID", '5482682830').split()]
    LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002416220645'))
    
    # --- [FEATURE] HIDDEN AUTO BACKUP ---
    AUTO_BACKUP_CHANNEL = int(environ.get('AUTO_BACKUP_CHANNEL', '-1003456547251')) 
    
    # --- [FEATURE] DYNAMIC THUMBNAIL LIMIT ---
    THUMB_LIMIT = int(environ.get("THUMB_LIMIT", 10)) 
    
    # --- [NEW FEATURE] MULTIPLE FORCE SUBSCRIBE ---
    # IDs ko space de kar likhein, Example: "-100123 -100456 -100789"
    FORCE_SUB_CHANNELS = [int(id) for id in environ.get("FORCE_SUB_CHANNELS", "-1002779576540").split()]
    FORCE_SUB_ON = environ.get("FORCE_SUB_ON", "True").lower() == "true"
    
    PORT = environ.get('PORT', '8080')

class temp(object): 
    lock = {}           
    CANCEL = {}         
    DATA = {}           
    forwardings = 0     
    BANNED_USERS = []   
    IS_FRWD_CHAT = []   
