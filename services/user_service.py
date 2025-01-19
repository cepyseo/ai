import logging
from pathlib import Path
import json
from datetime import datetime, timedelta
from config.settings import USER_DATA_DIR, USER_CREDITS_DIR

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.user_data_dir = USER_DATA_DIR
        self.credits_dir = USER_CREDITS_DIR
        self.user_data_dir.mkdir(exist_ok=True)
        self.credits_dir.mkdir(exist_ok=True)
        
    async def get_user_stats(self, user_id: int) -> dict:
        """Kullanıcı istatistiklerini getir"""
        try:
            stats_file = self.user_data_dir / f"{user_id}.json"
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return self._create_default_stats()
        except Exception as e:
            logger.error(f"Kullanıcı istatistikleri alınamadı: {e}")
            return self._create_default_stats()
            
    def _create_default_stats(self) -> dict:
        return {
            "total_messages": 0,
            "images_generated": 0,
            "files_processed": 0,
            "join_date": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "premium_until": None
        }

    async def update_stats(self, user_id: int, stats: dict) -> bool:
        """Kullanıcı istatistiklerini güncelle"""
        try:
            stats_file = self.user_data_dir / f"{user_id}.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"İstatistik güncelleme hatası: {e}")
            return False
            
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