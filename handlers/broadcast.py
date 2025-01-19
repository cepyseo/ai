import logging
from telegram import Update
from telegram.ext import ContextTypes
from config.settings import CHANNEL_USERNAME
from services.user_service import UserManager

logger = logging.getLogger(__name__)
user_manager = UserManager()

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, broadcast_msg: str):
    """Duyuru gönderme işlemi"""
    try:
        all_targets = await collect_targets(context)
        if not all_targets:
            return False, "Hedef bulunamadı"
            
        success, failed = await send_messages(context, all_targets, broadcast_msg)
        return True, (success, failed, len(all_targets))
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        return False, str(e)

async def collect_targets(context):
    """Hedef kullanıcıları topla"""
    all_targets = set()
    
    # Kullanıcıları topla...
    
    return all_targets 