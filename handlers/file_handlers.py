import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, THUMB_SIZE
from PIL import Image
import io
from utils.credits import check_credits, update_credits

logger = logging.getLogger(__name__)

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Dosya işleme fonksiyonu
    """
    try:
        if not update.message.document:
            return

        # Kredi kontrolü
        user_id = update.effective_user.id
        if not await check_credits(user_id, 'file_operations'):
            await update.message.reply_text(
                "❌ Yeterli krediniz yok!\n"
                "💡 Premium üyelik için: @Cepyseo"
            )
            return

        doc = update.message.document
        file_name = doc.file_name or "dosya"
        file_size = doc.file_size / (1024 * 1024)  # MB cinsinden

        # Dosya boyutu kontrolü
        if doc.file_size > MAX_FILE_SIZE:
            await update.message.reply_text(
                f"❌ Dosya çok büyük! Maksimum: {MAX_FILE_SIZE/(1024*1024):.1f}MB\n"
                f"📦 Dosya boyutu: {file_size:.1f}MB"
            )
            return

        # Dosya uzantısı kontrolü
        file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        if file_ext and file_ext not in ALLOWED_EXTENSIONS:
            await update.message.reply_text(
                f"❌ Desteklenmeyen dosya formatı!\n"
                f"💡 İzin verilen formatlar: {', '.join(ALLOWED_EXTENSIONS)}"
            )
            return

        # İşlem menüsü
        keyboard = [
            [
                InlineKeyboardButton("✏️ Yeniden Adlandır", callback_data=f"rename_{doc.file_id}"),
                InlineKeyboardButton("🖼️ Küçük Resim Ekle", callback_data=f"thumb_{doc.file_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Dosya bilgilerini göster
        await update.message.reply_text(
            f"📁 *Dosya Bilgileri*\n\n"
            f"📝 Ad: `{file_name}`\n"
            f"📦 Boyut: `{file_size:.1f} MB`\n"
            f"📎 Format: `{file_ext.upper() if file_ext else 'Bilinmiyor'}`\n\n"
            "💡 İşlem yapmak için butonları kullanın:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

        # Krediyi kullan
        await update_credits(user_id, 'file_operations', -1)

    except Exception as e:
        logger.error(f"Dosya işleme hatası: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Dosya işlenirken bir hata oluştu!\n"
            "Lütfen daha sonra tekrar deneyin."
        ) 