import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import (
    TelegramError, Unauthorized, BadRequest, 
    TimedOut, NetworkError
)

logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hataları yakala ve işle"""
    try:
        if update and update.effective_message:
            chat_id = update.effective_chat.id
            error = context.error
            
            if isinstance(error, Unauthorized):
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Bot'a erişim yetkiniz yok!"
                )
            elif isinstance(error, BadRequest):
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Geçersiz istek! Lütfen tekrar deneyin."
                )
            elif isinstance(error, TimedOut):
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⌛️ İstek zaman aşımına uğradı! Lütfen tekrar deneyin."
                )
            elif isinstance(error, NetworkError):
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🌐 Ağ hatası! Lütfen internet bağlantınızı kontrol edin."
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Bir hata oluştu! Lütfen daha sonra tekrar deneyin."
                )
                
            logger.error(f"Update {update} caused error {error}")
            
    except Exception as e:
        logger.error(f"Hata işleme hatası: {e}") 