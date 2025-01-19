import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import CHANNEL_USERNAME

logger = logging.getLogger(__name__)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback query'leri işle"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "commands":
        commands_text = (
            "📚 *Kullanılabilir Komutlar*\n\n"
            "🤖 *AI Komutları:*\n"
            "/ai - AI ile sohbet et\n"
            "/ai_clear - Sohbet geçmişini temizle\n"
            "/ai_history - Sohbet geçmişini göster\n\n"
            "🖼️ *Görsel Komutları:*\n"
            "/img - Görsel ara\n"
            "/thumb - Küçük resim ekle\n"
            "/del_thumb - Küçük resmi sil\n\n"
            "📊 *Diğer Komutlar:*\n"
            "/stats - İstatistiklerini gör\n"
            "/help - Yardım menüsü\n"
            "/premium - Premium bilgileri"
        )
        
        await query.message.edit_text(
            commands_text,
            parse_mode='Markdown'
        )
        
    elif query.data == "help":
        help_text = (
            "ℹ️ *Yardım Menüsü*\n\n"
            "1️⃣ Bot ile sohbet etmek için /ai komutunu kullanın\n"
            "2️⃣ Görsel aramak için /img <arama> şeklinde yazın\n"
            "3️⃣ Dosyalarınıza küçük resim eklemek için /thumb kullanın\n"
            "4️⃣ İstatistiklerinizi görmek için /stats yazın\n\n"
            "❓ Sorularınız için @clonicai ile iletişime geçin"
        )
        
        await query.message.edit_text(
            help_text,
            parse_mode='Markdown'
        ) 