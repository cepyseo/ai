import logging
from telegram import Update
from telegram.ext import ContextTypes
from config.settings import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, THUMB_SIZE
from PIL import Image
import io

logger = logging.getLogger(__name__)

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dosya işleme"""
    try:
        if update.message.document:
            file = update.message.document
            if file.file_size > MAX_FILE_SIZE:
                await update.message.reply_text("❌ Dosya boyutu çok büyük!")
                return
                
            # Dosya işleme kodları...
            
    except Exception as e:
        logger.error(f"Dosya işleme hatası: {e}")
        await update.message.reply_text("❌ Dosya işlenirken bir hata oluştu!") 