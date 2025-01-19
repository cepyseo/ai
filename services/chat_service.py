import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
from config.settings import CHAT_HISTORY_DIR

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.history_dir = CHAT_HISTORY_DIR
        self.history_dir.mkdir(exist_ok=True)
        self.max_history_age = timedelta(hours=24)
        self.max_messages = 50

    async def save_message(self, user_id: int, role: str, content: str):
        """Mesajı kaydet"""
        try:
            history_file = self.history_dir / f"{user_id}.json"
            messages = []
            
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
            
            # Eski mesajları temizle
            current_time = datetime.now()
            messages = [
                msg for msg in messages 
                if (current_time - datetime.fromisoformat(msg['timestamp'])) < self.max_history_age
            ]
            
            # Yeni mesajı ekle
            messages.append({
                'role': role,
                'content': content,
                'timestamp': current_time.isoformat()
            })
            
            # Son N mesajı tut
            messages = messages[-self.max_messages:]
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Mesaj kaydetme hatası: {e}")

    async def get_history(self, user_id: int) -> list:
        """Sohbet geçmişini getir"""
        try:
            history_file = self.history_dir / f"{user_id}.json"
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Geçmiş alma hatası: {e}")
            return []

    async def clear_history(self, user_id: int):
        """Sohbet geçmişini temizle"""
        try:
            history_file = self.history_dir / f"{user_id}.json"
            if history_file.exists():
                history_file.unlink()
        except Exception as e:
            logger.error(f"Geçmiş temizleme hatası: {e}") 