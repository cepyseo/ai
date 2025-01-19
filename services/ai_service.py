import logging
import json
from pathlib import Path
from config.settings import CHAT_HISTORY_DIR

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.history_dir = CHAT_HISTORY_DIR
        self.history_dir.mkdir(exist_ok=True)
    
    async def process_message(self, user_id: int, message: str):
        """Mesajı işle ve yanıt üret"""
        try:
            # AI işleme kodları...
            pass
        except Exception as e:
            logger.error(f"AI işleme hatası: {e}")
            return "Üzgünüm, bir hata oluştu." 