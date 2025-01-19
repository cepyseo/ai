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