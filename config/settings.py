import os
from pathlib import Path

# Bot ayarları
TOKEN = '7694637533:AAEz00Fc4lnLYqByt_56Bxr5YQqyPAlgosA'
CHANNEL_USERNAME = '@clonicai'

# Port ayarları
PORT = int(os.environ.get("PORT", 10000))

# Timeout ayarları
CONNECT_TIMEOUT = 60
READ_TIMEOUT = 60
WRITE_TIMEOUT = 60
POOL_TIMEOUT = 60

# Dizin yapılandırması
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
USER_DATA_DIR = DATA_DIR / "user_data"
CHAT_HISTORY_DIR = DATA_DIR / "chat_history"
USER_CREDITS_DIR = DATA_DIR / "user_credits"
BACKUP_DIR = DATA_DIR / "backups"
LANG_DIR = DATA_DIR / "lang"

# Dizinleri oluştur
for directory in [DATA_DIR, USER_DATA_DIR, CHAT_HISTORY_DIR, 
                 USER_CREDITS_DIR, BACKUP_DIR, LANG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Dosya işleme ayarları
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
THUMB_SIZE = (320, 320)

# Webhook ayarları
WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}" 