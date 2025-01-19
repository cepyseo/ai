import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import USER_DATA_DIR, CHANNEL_USERNAME
from services.user_service import UserManager

logger = logging.getLogger(__name__)
user_manager = UserManager()

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin paneli"""
    if not user_manager.is_admin(update.effective_user.username):
        await update.message.reply_text("⛔️ Admin yetkisine sahip değilsiniz!")
        return

    keyboard = [
        [
            InlineKeyboardButton("📢 Duyuru Yap", callback_data="admin_broadcast"),
            InlineKeyboardButton("👑 Premium Ver", callback_data="admin_premium")
        ],
        [
            InlineKeyboardButton("🚫 Kullanıcı Yasakla", callback_data="admin_ban"),
            InlineKeyboardButton("✅ Yasak Kaldır", callback_data="admin_unban")
        ],
        [
            InlineKeyboardButton("📊 İstatistikler", callback_data="admin_stats")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 *Admin Paneli*\n\n"
        "Yapmak istediğiniz işlemi seçin:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    ) 