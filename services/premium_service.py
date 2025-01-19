import logging
from datetime import datetime, timedelta
from config.settings import USER_DATA_DIR
from utils.helpers import save_json

logger = logging.getLogger(__name__)

class PremiumService:
    def __init__(self):
        self.user_data_dir = USER_DATA_DIR
        
    async def add_premium(self, user_id: int, days: int = 30) -> bool:
        """Kullanıcıya premium ver"""
        try:
            user_file = self.user_data_dir / f"{user_id}.json"
            user_data = {}
            
            if user_file.exists():
                with open(user_file, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
            
            current_premium = user_data.get('premium_until')
            if current_premium:
                premium_date = datetime.fromisoformat(current_premium)
                if premium_date > datetime.now():
                    premium_date += timedelta(days=days)
                else:
                    premium_date = datetime.now() + timedelta(days=days)
            else:
                premium_date = datetime.now() + timedelta(days=days)
            
            user_data['premium_until'] = premium_date.isoformat()
            save_json(user_data, user_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Premium ekleme hatası: {e}")
            return False 