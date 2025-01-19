import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.user_service import UserService
from services.language_service import LanguageService

logger = logging.getLogger(__name__)
user_service = UserService()
lang_service = LanguageService()

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ayarlar menüsü"""
    try:
        user_id = update.effective_user.id
        settings = await user_service.get_user_settings(user_id)
        
        settings_text = (
            "⚙️ *Kullanıcı Ayarları*\n\n"
            f"🌍 Dil: `{settings.get('language', 'Türkçe')}`\n"
            f"🔔 Bildirimler: `{'Açık' if settings.get('notifications', True) else 'Kapalı'}`\n"
            f"🕒 Saat Dilimi: `{settings.get('timezone', 'UTC+3')}`"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🌍 Dil Değiştir", callback_data="settings_language"),
                InlineKeyboardButton("🔔 Bildirimler", callback_data="settings_notifications")
            ],
            [
                InlineKeyboardButton("🕒 Saat Dilimi", callback_data="settings_timezone"),
                InlineKeyboardButton("↩️ Geri", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Ayarlar menüsü hatası: {e}")
        await update.message.reply_text("❌ Ayarlar menüsü yüklenirken bir hata oluştu!") 