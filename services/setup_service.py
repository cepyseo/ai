import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

def setup_project():
    """Proje yapısını oluşturur"""
    try:
        # Ana dizinler
        directories = [
            'config',
            'handlers',
            'services',
            'utils',
            'web',
            'data/user_data',
            'data/chat_history',
            'data/user_credits',
            'data/backups',
            'data/lang'
        ]
        
        # Dizinleri oluştur
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            init_file = Path(directory) / '__init__.py'
            if not init_file.exists():
                init_file.touch()
                
        logger.info("Proje yapısı başarıyla oluşturuldu")
        
    except Exception as e:
        logger.error(f"Proje yapısı oluşturulurken hata: {e}")
        raise 