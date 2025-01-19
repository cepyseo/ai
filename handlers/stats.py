import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.user_service import UserService

logger = logging.getLogger(__name__)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Kullanıcı istatistiklerini gösterir
    """
    try:
        user_id = update.effective_user.id
        user_service = UserService()
        stats = await user_service.get_user_stats(user_id)
        
        stats_text = (
            "📊 *İstatistikleriniz*\n\n"
            f"🤖 AI Sohbet Sayısı: {stats.get('ai_chats', 0)}\n"
            f"🖼️ İşlenen Dosya Sayısı: {stats.get('processed_files', 0)}\n"
            f"🔍 Görsel Arama Sayısı: {stats.get('image_searches', 0)}\n"
            f"💎 Kalan Kredileriniz: {stats.get('credits', 0)}"
        )
        
        await update.message.reply_text(
            stats_text,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"İstatistik gösterme hatası: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ İstatistikler gösterilirken bir hata oluştu!"
        ) 