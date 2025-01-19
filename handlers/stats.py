import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.user_service import UserService
from datetime import datetime

logger = logging.getLogger(__name__)
user_service = UserService()

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcı istatistiklerini göster"""
    try:
        user_id = update.effective_user.id
        stats = await user_service.get_user_stats(user_id)
        
        join_date = datetime.fromisoformat(stats['join_date'])
        last_active = datetime.fromisoformat(stats['last_active'])
        
        stats_message = (
            "📊 *Kullanıcı İstatistikleri*\n\n"
            f"📝 Toplam Mesaj: `{stats['total_messages']}`\n"
            f"🖼️ Oluşturulan Görsel: `{stats['images_generated']}`\n"
            f"📁 İşlenen Dosya: `{stats['files_processed']}`\n"
            f"📅 Katılım: `{join_date.strftime('%d.%m.%Y')}`\n"
            f"⏱️ Son Aktivite: `{last_active.strftime('%d.%m.%Y %H:%M')}`"
        )
        
        if stats['premium_until']:
            premium_until = datetime.fromisoformat(stats['premium_until'])
            stats_message += f"\n👑 Premium Bitiş: `{premium_until.strftime('%d.%m.%Y')}`"
            
        await update.message.reply_text(
            stats_message,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"İstatistik gösterme hatası: {e}")
        await update.message.reply_text("❌ İstatistikler alınırken bir hata oluştu!") 