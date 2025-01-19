import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import (
    TelegramError,
    TimedOut,
    NetworkError
)

logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Telegram bot hatalarını yönetir"""
    
    try:
        if update and update.effective_message:
            chat_id = update.effective_message.chat_id
        else:
            chat_id = None
            
        error = context.error
        
        if isinstance(error, TimedOut):
            logger.warning(f"Timeout hatası: {error}")
            if chat_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ İşlem zaman aşımına uğradı. Lütfen tekrar deneyin."
                )
                
        elif isinstance(error, NetworkError):
            logger.error(f"Ağ hatası: {error}")
            if chat_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="📶 Bağlantı sorunu oluştu. Lütfen daha sonra tekrar deneyin."
                )
                
        else:
            logger.error(f"Bot hatası: {error}", exc_info=context.error)
            if chat_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Bir hata oluştu. Lütfen daha sonra tekrar deneyin."
                )
                
    except Exception as e:
        logger.error(f"Hata yönetimi sırasında hata: {e}", exc_info=True) 