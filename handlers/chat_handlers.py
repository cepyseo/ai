import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.chat_service import ChatService
from services.user_service import UserService
from admin_utils import UserManager
from datetime import datetime
from utils.credits import check_credits, update_credits
from handlers.admin_handlers import handle_admin_actions

logger = logging.getLogger(__name__)
chat_service = ChatService()
user_service = UserService()
user_manager = UserManager()

async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Normal sohbet mesajlarını işler
    """
    try:
        message = update.message.text
        user_id = update.effective_user.id
        
        # Admin işlemlerini kontrol et
        if 'admin_state' in context.user_data:
            if user_manager.is_admin(update.effective_user.username):
                await handle_admin_actions(update, context)
            return
            
        # Özel sohbet kontrolü
        if update.effective_chat.type != 'private':
            # Grup mesajlarını yoksay
            return
            
        # Yasaklı kullanıcı kontrolü
        if user_manager.is_banned(user_id):
            await update.message.reply_text("⛔️ Bottan yasaklandınız!")
            return
            
        # AI sohbet durumunu kontrol et
        if not context.user_data.get('ai_chat_active'):
            # AI sohbet aktif değilse, yoksay
            return
            
        # Kredi kontrolü
        if not await check_credits(user_id, 'ai_chat'):
            await update.message.reply_text(
                "❌ Yetersiz kredi!\n"
                "Kredi satın almak için @clonicai ile iletişime geçin."
            )
            return
            
        # Bekleme mesajı gönder
        wait_message = await update.message.reply_text(
            "🤔 Düşünüyorum...",
            parse_mode='Markdown'
        )
            
        # Mesajı işle
        response = await chat_service.process_message(user_id, message)
        
        # Bekleme mesajını sil
        await wait_message.delete()
        
        # Yanıt gönder
        await update.message.reply_text(
            f"🤖 *AI Yanıtı:*\n\n{response}",
            parse_mode='Markdown'
        )
        
        # Kullanıcı istatistiklerini güncelle
        stats = await user_service.get_user_stats(user_id)
        stats['total_messages'] += 1
        stats['last_active'] = datetime.now().isoformat()
        await user_service.update_stats(user_id, stats)
        
        # Krediyi düş
        await update_credits(user_id, 'ai_chat', -1)
        
    except Exception as e:
        logger.error(f"Sohbet işleme hatası: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Mesajınız işlenirken bir hata oluştu!"
        ) 