import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import CHANNEL_USERNAME

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Başlangıç komutu"""
    user = update.effective_user
    first_name = user.first_name if user.first_name else "Değerli Kullanıcı"

    welcome_message = (
        f"🎉 *Merhaba {first_name}!*\n\n"
        "Ben *ClonicAI Bot*, yapay zeka destekli çok yönlü bir asistanım. "
        "Size aşağıdaki konularda yardımcı olabilirim:\n\n"
        "🤖 *AI Sohbet*\n"
        "• Yapay zeka ile sohbet edebilir\n"
        "• Sorularınıza detaylı yanıtlar alabilir\n"
        "• 24 saat sohbet geçmişi tutabilirsiniz\n\n"
        "🖼️ *Görsel İşlemler*\n"
        "• Yüksek kaliteli görseller arayabilir\n"
        "• Dosyalarınıza küçük resim ekleyebilir\n"
        "• Dosya adlarını düzenleyebilirsiniz"
    )

    keyboard = [
        [
            InlineKeyboardButton("📚 Komutlar", callback_data="commands"),
            InlineKeyboardButton("ℹ️ Yardım", callback_data="help")
        ],
        [
            InlineKeyboardButton("📢 Kanal", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"),
            InlineKeyboardButton("👨‍💻 Geliştirici", url="https://t.me/clonicai")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    ) 