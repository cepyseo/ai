import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.backup_service import BackupService
from services.user_service import UserService
from datetime import datetime

logger = logging.getLogger(__name__)
backup_service = BackupService()
user_service = UserService()

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin dashboard"""
    try:
        if not user_service.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔️ Bu komutu kullanma yetkiniz yok!")
            return
            
        # İstatistikleri al
        total_users = await user_service.get_total_users()
        active_users = await user_service.get_active_users_today()
        premium_users = await user_service.get_premium_users()
        
        dashboard_text = (
            "📊 *Admin Dashboard*\n\n"
            f"👥 Toplam Kullanıcı: `{total_users}`\n"
            f"📱 Aktif Kullanıcı: `{active_users}`\n"
            f"👑 Premium Üye: `{premium_users}`\n\n"
            "Son Yedekleme:\n"
            f"🗓 {await get_last_backup_date()}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Yedek Al", callback_data="admin_backup"),
                InlineKeyboardButton("📊 Detaylı İstatistik", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("👥 Kullanıcı Listesi", callback_data="admin_users"),
                InlineKeyboardButton("⚙️ Ayarlar", callback_data="admin_settings")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            dashboard_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Dashboard hatası: {e}")
        await update.message.reply_text("❌ Dashboard yüklenirken bir hata oluştu!")

async def get_last_backup_date() -> str:
    """Son yedekleme tarihini getir"""
    try:
        backup_files = list(BACKUP_DIR.glob('backup_*'))
        if not backup_files:
            return "Henüz yedek yok"
            
        latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
        backup_time = datetime.fromtimestamp(latest_backup.stat().st_mtime)
        return backup_time.strftime('%d.%m.%Y %H:%M')
        
    except Exception as e:
        logger.error(f"Yedek tarihi alma hatası: {e}")
        return "Bilinmiyor" 