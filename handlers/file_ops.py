import logging
from telegram import Update
from telegram.ext import ContextTypes
from config.settings import FREEMIUM_FILE_SIZE, PREMIUM_FILE_SIZE, THUMB_SIZE
from PIL import Image
import io
from services.user_service import get_user_data

logger = logging.getLogger(__name__)

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dosya işleme"""
    try:
        if update.message.document:
            # Kullanıcı bilgilerini al
            user_id = update.effective_user.id
            user_data = get_user_data(user_id)
            is_premium = user_data.get('is_premium', False)
            
            # Dosya boyutu limiti belirle
            max_file_size = PREMIUM_FILE_SIZE if is_premium else FREEMIUM_FILE_SIZE
            
            file = update.message.document
            file_size = file.file_size / (1024 * 1024)  # MB cinsinden
            
            if file.file_size > max_file_size:
                limit_text = "1.5GB" if is_premium else "100MB"
                await update.message.reply_text(
                    f"❌ Dosya çok büyük! {'' if is_premium else 'Freemium kullanıcı limitiniz: 100MB'}\n"
                    f"📦 Dosya boyutu: {file_size:.1f}MB\n"
                    f"{'💎 Premium kullanıcı limitiniz: 1.5GB' if is_premium else '💎 Premium üyelik ile 1.5GB\'a kadar dosya yükleyebilirsiniz!'}\n"
                    f"{'⚠️ Premium üye olduğunuz halde bu hatayı görüyorsanız @Cepyseo ile iletişime geçin.' if is_premium else '💡 Premium üyelik için: @Cepyseo'}"
                )
                return
                
            # Dosya işleme kodları...
            
    except Exception as e:
        logger.error(f"Dosya işleme hatası: {e}")
        await update.message.reply_text("❌ Dosya işlenirken bir hata oluştu!") 