import logging
from pathlib import Path
import io
from PIL import Image
from config.settings import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, THUMB_SIZE

logger = logging.getLogger(__name__)

class FileService:
    @staticmethod
    async def process_image(image_data: bytes, filename: str) -> tuple:
        """Görsel işle"""
        try:
            # Görsel boyutunu kontrol et
            if len(image_data) > MAX_FILE_SIZE:
                return False, "Dosya boyutu çok büyük!"
            
            # Dosya uzantısını kontrol et
            ext = filename.split('.')[-1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                return False, "Desteklenmeyen dosya formatı!"
            
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
            return False, "Görsel işlenirken bir hata oluştu!"

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