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
WEBHOOK_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if not WEBHOOK_HOST:
    raise ValueError("RENDER_EXTERNAL_HOSTNAME environment variable is not set!")

WEBHOOK_PATH = f'/{TOKEN}'
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBHOOK_MAX_CONNECTIONS = 100

# Web sunucu ayarları
WEB_SERVER = {
    'host': '0.0.0.0',
    'port': int(os.environ.get("PORT", 10000)),
    'webhook_path': WEBHOOK_PATH,
}

# Debug modu
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Logging ayarları
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True
        },
    }
} 