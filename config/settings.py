import os
from pathlib import Path

# Bot ayarları
TOKEN = '7694637533:AAEz00Fc4lnLYqByt_56Bxr5YQqyPAlgosA'
TELEGRAM_TOKEN = TOKEN  # Eski kodlarla uyumluluk için
CHANNEL_USERNAME = '@clonicai'

# Port ayarları
PORT = int(os.environ.get("PORT", 10000))

# Timeout ayarları
CONNECT_TIMEOUT = 30.0
READ_TIMEOUT = 30.0
WRITE_TIMEOUT = 30.0
POOL_TIMEOUT = 30.0

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
FREEMIUM_FILE_SIZE = 100 * 1024 * 1024  # 100MB
PREMIUM_FILE_SIZE = 1.5 * 1024 * 1024 * 1024  # 1.5GB
THUMB_SIZE = (320, 320)

# Webhook ve port ayarları
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
RENDER_PORT = int(os.environ.get('PORT', 10000))

# Webhook yapılandırması
if RENDER_EXTERNAL_URL:
    # URL'i temizle ve formatla
    RENDER_EXTERNAL_URL = RENDER_EXTERNAL_URL.replace('https://', '').replace('http://', '').rstrip('/')
    WEBHOOK_URL = f"https://{RENDER_EXTERNAL_URL}/{TOKEN}"
    WEBHOOK_SECRET = "".join(c for c in TOKEN[:20] if c.isalnum())  # Sadece alfanumerik karakterler
else:
    WEBHOOK_URL = None
    WEBHOOK_SECRET = None

# Chat ayarları
MAX_HISTORY_AGE = 24 * 60 * 60  # 24 saat (saniye cinsinden)
MAX_HISTORY_LENGTH = 10  # Maksimum kaç mesaj hatırlansın

# API limitleri
MAX_CONNECTIONS = 40  # Render Free tier için optimize edildi

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