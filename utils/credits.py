import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

async def check_credits(user_id: int, feature: str) -> bool:
    """Kullanıcının yeterli kredisi var mı kontrol eder"""
    try:
        credits_dir = Path("data/user_credits")
        credits_file = credits_dir / f"{user_id}.json"
        
        if not credits_file.exists():
            # Yeni kullanıcı için kredi dosyası oluştur
            credits_data = {"credits": 10}  # Başlangıç kredisi
            credits_dir.mkdir(parents=True, exist_ok=True)
            with open(credits_file, 'w', encoding='utf-8') as f:
                json.dump(credits_data, f)
            return True
            
        with open(credits_file, 'r', encoding='utf-8') as f:
            credits_data = json.load(f)
            
        return credits_data.get("credits", 0) > 0
        
    except Exception as e:
        logger.error(f"Kredi kontrolü hatası: {e}", exc_info=True)
        return False

async def update_credits(user_id: int, feature: str, amount: int):
    """Kullanıcının kredilerini günceller"""
    try:
        credits_dir = Path("data/user_credits")
        credits_file = credits_dir / f"{user_id}.json"
        
        if credits_file.exists():
            with open(credits_file, 'r', encoding='utf-8') as f:
                credits_data = json.load(f)
        else:
            credits_data = {"credits": 0}
            
        credits_data["credits"] = max(0, credits_data.get("credits", 0) + amount)
        
        with open(credits_file, 'w', encoding='utf-8') as f:
            json.dump(credits_data, f)
            
    except Exception as e:
        logger.error(f"Kredi güncelleme hatası: {e}", exc_info=True)
        raise 