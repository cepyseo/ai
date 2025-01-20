import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import FREEMIUM_FILE_SIZE, PREMIUM_FILE_SIZE, THUMB_SIZE
from PIL import Image
import io
from utils.credits import check_credits, update_credits
from services.user_service import get_user_data

logger = logging.getLogger(__name__)

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Dosya işleme fonksiyonu
    """
    try:
        if not update.message.document:
            return

        # Kullanıcı bilgilerini al
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        is_premium = user_data.get('is_premium', False)
        
        # Dosya boyutu limiti belirle
        max_file_size = PREMIUM_FILE_SIZE if is_premium else FREEMIUM_FILE_SIZE

        # Kredi kontrolü
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
        if doc.file_size > max_file_size:
            limit_text = "1.5GB" if is_premium else "100MB"
            await update.message.reply_text(
                f"❌ Dosya çok büyük! {'' if is_premium else 'Freemium kullanıcı limitiniz: 100MB'}\n"
                f"📦 Dosya boyutu: {file_size:.1f}MB\n"
                f"{'💎 Premium kullanıcı limitiniz: 1.5GB' if is_premium else '💎 Premium üyelik ile 1.5GB\'a kadar dosya yükleyebilirsiniz!'}\n"
                f"{'⚠️ Premium üye olduğunuz halde bu hatayı görüyorsanız @Cepyseo ile iletişime geçin.' if is_premium else '💡 Premium üyelik için: @Cepyseo'}"
            )
            return

        # Dosya uzantısını al
        file_ext = file_name.split('.')[-1].lower() if '.' in file_name else 'bilinmiyor'

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
            f"📎 Format: `{file_ext.upper()}`\n"
            f"👤 Hesap: {'💎 Premium' if is_premium else '🆓 Freemium'}\n\n"
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