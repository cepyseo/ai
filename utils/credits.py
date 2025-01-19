import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

async def check_credits(user_id: int, action: str) -> bool:
    """Kredi kontrolü yap"""
    try:
        credits_file = Path(f"data/user_credits/{user_id}.json")
        if not credits_file.exists():
            return False
            
        with open(credits_file, 'r') as f:
            credits = json.load(f)
            return credits.get(action, 0) > 0
            
    except Exception as e:
        logger.error(f"Kredi kontrolü hatası: {e}")
        return False

async def update_credits(user_id: int, action: str, amount: int) -> bool:
    """Kredi güncelle"""
    try:
        credits_file = Path(f"data/user_credits/{user_id}.json")
        credits = {}
        
        if credits_file.exists():
            with open(credits_file, 'r') as f:
                credits = json.load(f)
                
        if action not in credits:
            credits[action] = 0
            
        credits[action] += amount
        
        with open(credits_file, 'w') as f:
            json.dump(credits, f)
            
        return True
        
    except Exception as e:
        logger.error(f"Kredi güncelleme hatası: {e}")
        return False 