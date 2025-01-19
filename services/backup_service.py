import logging
import json
import shutil
from pathlib import Path
from datetime import datetime
from config.settings import (
    USER_DATA_DIR, 
    CHAT_HISTORY_DIR, 
    USER_CREDITS_DIR,
    BACKUP_DIR
)

logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(exist_ok=True)
        
    async def create_backup(self) -> bool:
        """Tüm verilerin yedeğini al"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f"backup_{timestamp}"
            backup_path.mkdir(exist_ok=True)
            
            # Kullanıcı verilerini yedekle
            self._backup_directory(USER_DATA_DIR, backup_path / "user_data")
            self._backup_directory(CHAT_HISTORY_DIR, backup_path / "chat_history")
            self._backup_directory(USER_CREDITS_DIR, backup_path / "user_credits")
            
            # Yedek meta verilerini kaydet
            meta = {
                'timestamp': timestamp,
                'total_users': len(list(USER_DATA_DIR.glob('*.json'))),
                'total_chats': len(list(CHAT_HISTORY_DIR.glob('*.json'))),
                'backup_version': '1.0'
            }
            
            with open(backup_path / 'meta.json', 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Yedekleme hatası: {e}")
            return False
            
    def _backup_directory(self, src: Path, dst: Path):
        """Klasörü yedekle"""
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True) 