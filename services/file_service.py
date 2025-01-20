import logging
from pathlib import Path
import io
from PIL import Image
from config.settings import FREEMIUM_FILE_SIZE, PREMIUM_FILE_SIZE, THUMB_SIZE
from services.user_service import get_user_data

logger = logging.getLogger(__name__)

class FileService:
    @staticmethod
    async def process_image(image_data: bytes, filename: str, user_id: int) -> tuple:
        """Görsel işle"""
        try:
            # Kullanıcı bilgilerini al
            user_data = get_user_data(user_id)
            is_premium = user_data.get('is_premium', False)
            
            # Dosya boyutu limiti belirle
            max_file_size = PREMIUM_FILE_SIZE if is_premium else FREEMIUM_FILE_SIZE
            
            # Görsel boyutunu kontrol et
            if len(image_data) > max_file_size:
                limit_text = "1.5GB" if is_premium else "100MB"
                return False, f"❌ Dosya çok büyük! {'' if is_premium else 'Freemium kullanıcı limitiniz: 100MB'}\n" \
                           f"📦 Dosya boyutu: {len(image_data)/(1024*1024):.1f}MB\n" \
                           f"{'💎 Premium kullanıcı limitiniz: 1.5GB' if is_premium else '💎 Premium üyelik ile 1.5GB\'a kadar dosya yükleyebilirsiniz!'}\n" \
                           f"{'⚠️ Premium üye olduğunuz halde bu hatayı görüyorsanız @Cepyseo ile iletişime geçin.' if is_premium else '💡 Premium üyelik için: @Cepyseo'}"
            
            # Görseli aç ve küçük resim oluştur
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail(THUMB_SIZE)
            
            # Küçük resmi byte dizisine çevir
            thumb_io = io.BytesIO()
            image.save(thumb_io, format='JPEG')
            thumb_io.seek(0)
            
            return True, thumb_io.getvalue()
            
        except Exception as e:
            logger.error(f"Görsel işleme hatası: {e}")
            return False, "❌ Görsel işlenirken bir hata oluştu!"

    @staticmethod
    async def validate_filename(filename: str) -> bool:
        """Dosya adını doğrula"""
        try:
            # Geçersiz karakterleri kontrol et
            invalid_chars = '<>:"/\\|?*'
            return not any(char in filename for char in invalid_chars)
        except Exception as e:
            logger.error(f"Dosya adı doğrulama hatası: {e}")
            return False 