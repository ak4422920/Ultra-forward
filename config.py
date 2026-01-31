import os
import datetime
from os import environ 

class Config:
    # --- BASIC BOT SETTINGS ---
    API_ID = int(environ.get("API_ID", "29171167")) 
    API_HASH = environ.get("API_HASH", "7ea2149629e445936619f06a3c0dc716") 
    BOT_TOKEN = environ.get("BOT_TOKEN", "") 
    BOT_SESSION = environ.get("BOT_SESSION", "AutoForwarder_V3") 
    
    # --- DATABASE SETTINGS ---
    DATABASE_URI = environ.get("DATABASE_URI", environ.get("DATABASE", "mongodb+srv://for:for@cluster0.fgu4b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")) 
    DATABASE_NAME = environ.get("DATABASE_NAME", "Cluster0")
    
    # --- ADMIN & LOGGING ---
    # Multiple IDs space dekar daal sakte hain
    BOT_OWNER_ID = [int(id) for id in environ.get("BOT_OWNER_ID", "5482682830").split()]
    LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002416220645'))
    
    # --- [FEATURE] HIDDEN AUTO BACKUP (Feature 15) ---
    AUTO_BACKUP_CHANNEL = int(environ.get('AUTO_BACKUP_CHANNEL', '-1003456547251')) 
    
    # --- [FEATURE] DYNAMIC THUMBNAIL LIMIT ---
    THUMB_LIMIT = int(environ.get("THUMB_LIMIT", 10)) 
    
    # --- [NEW FEATURE] MULTIPLE FORCE SUBSCRIBE (Feature 13) ---
    # 1. FORCE_SUB_CHANNELS (Logic check ke liye list)
    FORCE_SUB_CHANNELS = [int(id) for id in environ.get("FORCE_SUB_CHANNELS", "-1002779576540").split()]
    
    # 2. FORCE_SUB_CHANNEL (Buttons ke liye original URL)
    FORCE_SUB_CHANNEL = environ.get("FORCE_SUB_CHANNEL", "https://t.me/AkMovieVerse") 
    
    FORCE_SUB_ON = environ.get("FORCE_SUB_ON", "True").lower() == "true"
    
    # --- WEB SERVER PORT ---
    PORT = environ.get('PORT', '8080')

class temp(object): 
    lock = {}           # Multiple tasks per user rokne ke liye
    CANCEL = {}         # Tasks stop karne ke liye
    DATA = {}           
    forwardings = 0     # Active tasks count stats ke liye
    BANNED_USERS = []   
    IS_FRWD_CHAT = []

    # --- [NEW] TASK MANAGEMENT STATES ---
    LIVE_TASKS = {}     # Feature 1: Live Forwarding track karne ke liye
    RESUME_TASKS = {}   # Feature 3: Auto-Resume states save karne ke liye
    
    # --- [NEW] WORKER STATE ---
    ACTIVE_WORKERS = {} # Feature 12: Multiple sessions manage karne ke liye
