import logging
from telegram import Update
from telegram.ext import ContextTypes
from config.settings import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, THUMB_SIZE
from PIL import Image
import io

logger = logging.getLogger(__name__)

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Dosya işleme fonksiyonu
    """
    try:
        if update.message.document:
            file = update.message.document
            if file.file_size > MAX_FILE_SIZE:
                await update.message.reply_text(
                    "❌ Dosya boyutu çok büyük! Maksimum boyut: 10MB"
                )
                return

            file_ext = file.file_name.split('.')[-1].lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                await update.message.reply_text(
                    f"❌ Desteklenmeyen dosya formatı! İzin verilen formatlar: {', '.join(ALLOWED_EXTENSIONS)}"
                )
                return

            await update.message.reply_text("✅ Dosya başarıyla işlendi!")

    except Exception as e:
        logger.error(f"Dosya işleme hatası: {e}", exc_info=True)
        await update.message.reply_text("❌ Dosya işlenirken bir hata oluştu!") 