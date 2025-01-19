import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.chat_service import ChatService
from services.user_service import UserService
from datetime import datetime

logger = logging.getLogger(__name__)
chat_service = ChatService()
user_service = UserService()

async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sohbet mesajlarını işle"""
    try:
        user_id = update.effective_user.id
        message = update.message.text
        
        # Kullanıcı mesajını kaydet
        await chat_service.save_message(user_id, 'user', message)
        
        # Kullanıcı istatistiklerini güncelle
        stats = await user_service.get_user_stats(user_id)
        stats['total_messages'] += 1
        stats['last_active'] = datetime.now().isoformat()
        await user_service.update_stats(user_id, stats)
        
        # Bot yanıtını hazırla ve kaydet
        response = "Mesajınız alındı!"  # Burada AI yanıtı gelecek
        await chat_service.save_message(user_id, 'assistant', response)
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Sohbet işleme hatası: {e}")
        await update.message.reply_text("❌ Mesajınız işlenirken bir hata oluştu!") 