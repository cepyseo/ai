import logging
import json
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from config.settings import CHAT_HISTORY_DIR

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.chat_dir = CHAT_HISTORY_DIR
        self.chat_dir.mkdir(exist_ok=True)
        self.max_history_age = timedelta(hours=24)
        self.max_messages = 50

    async def get_ai_response(self, message: str) -> str:
        """AI'dan yanıt al"""
        try:
            # API isteği için parametreleri hazırla
            api_url = "https://darkness.ashlynn.workers.dev/chat/"
            params = {
                "prompt": message,
                "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                "stream": "false",
                "temperature": 0.7
            }
            
            # API isteği gönder
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.get(
                    api_url,
                    params=params,
                    headers={
                        'User-Agent': 'Mozilla/5.0',
                        'Accept': 'application/json'
                    }
                )
                response.raise_for_status()
                data = response.json()
            
            # Yanıtı işle
            if isinstance(data, str):
                return data
            elif isinstance(data, dict) and data.get("response"):
                return data['response']
            else:
                return "❌ Üzgünüm, yanıt alınamadı."
                
        except Exception as e:
            logger.error(f"AI yanıt alma hatası: {e}")
            return "❌ Yanıt alınırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."

    async def save_message(self, user_id: int, role: str, content: str):
        """Mesajı kaydet"""
        try:
            history_file = self.chat_dir / f"{user_id}.json"
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
        """Kullanıcının sohbet geçmişini getir"""
        try:
            history_file = self.chat_dir / f"{user_id}.json"
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('messages', [])
            return []
        except Exception as e:
            logger.error(f"Sohbet geçmişi alma hatası: {e}")
            return []

    async def clear_history(self, user_id: int) -> bool:
        """Kullanıcının sohbet geçmişini temizle"""
        try:
            history_file = self.chat_dir / f"{user_id}.json"
            if history_file.exists():
                history_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Sohbet geçmişi temizleme hatası: {e}")
            return False

    async def process_message(self, user_id: int, message: str) -> str:
        """Kullanıcı mesajını işle ve yanıt döndür"""
        try:
            # Mesajı geçmişe ekle
            await self.save_message(user_id, 'user', message)
            
            # AI yanıtını al
            response = await self.get_ai_response(message)
            
            # Yanıtı geçmişe ekle
            await self.save_message(user_id, 'assistant', response)
            
            return response
            
        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {e}")
            return "❌ Mesajınız işlenirken bir hata oluştu!" 