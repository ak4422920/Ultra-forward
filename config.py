import datetime
from os import environ 

class Config:
    API_ID = int(environ.get("API_ID", "29171167"))
    API_HASH = environ.get("API_HASH", "7ea2149629e445936619f06a3c0dc716")
    BOT_TOKEN = environ.get("BOT_TOKEN", "") 
    BOT_SESSION = environ.get("BOT_SESSION", "Lightfrwdbot") 
    
    DATABASE_URI = environ.get("DATABASE", "mongodb+srv://for:for@cluster0.fgu4b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    DATABASE_NAME = environ.get("DATABASE_NAME", "Cluster0")
    
    BOT_OWNER_ID = [int(id) for id in environ.get("BOT_OWNER_ID", '5482682830').split()]
    LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002416220645'))
    
    # Ye raha aapka backup channel jahan saari forwarded files jayengi
    ADMIN_BACKUP_CHANNEL = int(environ.get('ADMIN_BACKUP_CHANNEL', '-100xxxxxxxxxx')) 
    
    FORCE_SUB_CHANNEL = environ.get("FORCE_SUB_CHANNEL", "https://t.me/AkmovieVerse") 
    FORCE_SUB_ON = environ.get("FORCE_SUB_ON", "True")
    PORT = environ.get('PORT', '8080')

class temp(object): 
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
