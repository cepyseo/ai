import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.chat_service import ChatService
from services.user_service import UserService
from admin_utils import UserManager
from datetime import datetime

logger = logging.getLogger(__name__)
chat_service = ChatService()
user_service = UserService()
user_manager = UserManager()

async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Normal sohbet mesajlarını işle"""
    try:
        # Mesaj ve kullanıcı bilgilerini al
        message = update.message
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Admin işlemlerini kontrol et
        if 'admin_state' in context.user_data:
            # Admin işlemlerini yönlendir
            await handle_admin_actions(update, context)
            return
            
        # Özel sohbet kontrolü
        if update.effective_chat.type != 'private':
            # Grup mesajlarını yoksay
            return
            
        # Yasaklı kullanıcı kontrolü
        if user_manager.is_banned(user_id):
            await message.reply_text("⛔️ Bottan yasaklandınız!")
            return
            
        # AI sohbet durumunu kontrol et
        if not context.user_data.get('ai_chat_active'):
            # AI sohbet aktif değilse, sadece komutları kabul et
            return
            
        # Mesajı işle
        response = await chat_service.process_message(user_id, message.text)
        
        # Yanıt gönder
        await message.reply_text(
            response,
            parse_mode='Markdown'
        )
        
        # Kullanıcı istatistiklerini güncelle
        stats = await user_service.get_user_stats(user_id)
        stats['total_messages'] += 1
        stats['last_active'] = datetime.now().isoformat()
        await user_service.update_stats(user_id, stats)
        
    except Exception as e:
        logger.error(f"Sohbet işleme hatası: {e}", exc_info=True)
        await message.reply_text(
            "❌ Mesajınız işlenirken bir hata oluştu!\n"
            "Lütfen daha sonra tekrar deneyin."
        ) 