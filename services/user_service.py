import logging
from pathlib import Path
import json
from datetime import datetime, timedelta
from config.settings import USER_DATA_DIR, USER_CREDITS_DIR

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.user_data_dir = Path("data/user_data")
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.credits_dir = USER_CREDITS_DIR
        self.credits_dir.mkdir(exist_ok=True)
        
    async def get_user_stats(self, user_id: int) -> dict:
        """Kullanıcı istatistiklerini getirir"""
        try:
            stats_file = self.user_data_dir / f"{user_id}.json"
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                'ai_chats': 0,
                'processed_files': 0,
                'image_searches': 0,
                'credits': 10,  # Yeni kullanıcılar için başlangıç kredisi
                'total_messages': 0,
                'last_active': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Kullanıcı istatistikleri getirme hatası: {e}", exc_info=True)
            raise
            
    async def update_stats(self, user_id: int, stats: dict):
        """Kullanıcı istatistiklerini günceller"""
        try:
            stats_file = self.user_data_dir / f"{user_id}.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"İstatistik güncelleme hatası: {e}", exc_info=True)
            raise
            
    async def get_all_users(self) -> list:
        """Tüm kullanıcı ID'lerini getir"""
        try:
            users = set()
            
            # User data klasöründen kullanıcıları al
            for file in self.user_data_dir.glob("*.json"):
                try:
                    user_id = int(file.stem)
                    users.add(user_id)
                except ValueError:
                    continue
                    
            # Credits klasöründen kullanıcıları al
            for file in self.credits_dir.glob("*.json"):
                try:
                    user_id = int(file.stem)
                    users.add(user_id)
                except ValueError:
                    continue
                    
            return list(users)
            
        except Exception as e:
            logger.error(f"Kullanıcı listesi alma hatası: {e}")
            return []
            
    async def get_premium_users(self) -> int:
        """Premium kullanıcı sayısını getir"""
        try:
            premium_count = 0
            for user_id in await self.get_all_users():
                stats = await self.get_user_stats(user_id)
                if stats.get('premium_until'):
                    premium_until = datetime.fromisoformat(stats['premium_until'])
                    if premium_until > datetime.now():
                        premium_count += 1
            return premium_count
        except Exception as e:
            logger.error(f"Premium kullanıcı sayısı alma hatası: {e}")
            return 0
            
    async def get_active_users_today(self) -> int:
        """Bugün aktif olan kullanıcı sayısını getir"""
        try:
            today = datetime.now().date()
            active_users = 0
            
            for user_id in await self.get_all_users():
                stats = await self.get_user_stats(user_id)
                last_active = datetime.fromisoformat(stats.get('last_active', '')).date()
                if last_active == today:
                    active_users += 1
                    
            return active_users
        except Exception as e:
            logger.error(f"Aktif kullanıcı sayısı alma hatası: {e}")
            return 0
            
    async def get_total_users(self) -> int:
        """Toplam kullanıcı sayısını getir"""
        return len(await self.get_all_users()) 