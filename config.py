import os
from os import environ 

class Config:
    # --- BASIC BOT SETTINGS ---
    API_ID = int(environ.get("API_ID", "12345")) # Replace with your API ID
    API_HASH = environ.get("API_HASH", "your_api_hash") 
    BOT_TOKEN = environ.get("BOT_TOKEN", "") 
    BOT_SESSION = environ.get("BOT_SESSION", "AutoForwarder_V3") 
    
    # --- DATABASE SETTINGS ---
    DATABASE_URI = environ.get("DATABASE_URI", environ.get("DATABASE", "")) 
    DATABASE_NAME = environ.get("DATABASE_NAME", "Cluster0")
    
    # --- ADMIN & LOGGING ---
    # Isme multiple IDs space dekar daal sakte hain
    BOT_OWNER_ID = [int(id) for id in environ.get("BOT_OWNER_ID", "5482682830").split()]
    LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002416220645'))
    
    # --- [FEATURE] HIDDEN AUTO BACKUP ---
    AUTO_BACKUP_CHANNEL = int(environ.get('AUTO_BACKUP_CHANNEL', '-1003456547251')) 
    
    # --- [FEATURE] DYNAMIC THUMBNAIL LIMIT ---
    THUMB_LIMIT = int(environ.get("THUMB_LIMIT", 10)) 
    
    # --- [NEW FEATURE] MULTIPLE FORCE SUBSCRIBE ---
    # 1. FORCE_SUB_CHANNELS (List of IDs for Logic check)
    FORCE_SUB_CHANNELS = [int(id) for id in environ.get("FORCE_SUB_CHANNELS", "-1002779576540").split()]
    
    # 2. FORCE_SUB_CHANNEL (Single URL for Buttons) - [FIXED MISSING ATTR]
    FORCE_SUB_CHANNEL = environ.get("FORCE_SUB_CHANNEL", "https://t.me/AkMovieVerse") 
    
    FORCE_SUB_ON = environ.get("FORCE_SUB_ON", "True").lower() == "true"
    
    # --- WEB SERVER PORT ---
    PORT = environ.get('PORT', '8080')

class temp(object): 
    lock = {}           # To prevent multiple tasks per user
    CANCEL = {}         # To stop ongoing tasks
    DATA = {}           
    forwardings = 0     # Active tasks count for stats
    BANNED_USERS = []   
    IS_FRWD_CHAT = []
