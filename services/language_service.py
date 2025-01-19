import logging
import json
from pathlib import Path
from config.settings import LANG_DIR

logger = logging.getLogger(__name__)

class LanguageService:
    def __init__(self):
        self.lang_dir = LANG_DIR
        self.lang_dir.mkdir(exist_ok=True)
        self.default_lang = 'tr'
        self.translations = {}
        self._load_translations()
        
    def _load_translations(self):
        """Dil dosyalarını yükle"""
        try:
            for lang_file in self.lang_dir.glob('*.json'):
                lang_code = lang_file.stem
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
        except Exception as e:
            logger.error(f"Dil dosyası yükleme hatası: {e}")
            
    def get_text(self, key: str, lang: str = None) -> str:
        """Metni getir"""
        try:
            lang = lang or self.default_lang
            if lang in self.translations and key in self.translations[lang]:
                return self.translations[lang][key]
            return self.translations[self.default_lang].get(key, key)
        except Exception as e:
            logger.error(f"Metin getirme hatası: {e}")
            return key 