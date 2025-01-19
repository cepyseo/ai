import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

def save_json(data: dict, file_path: Path):
    """JSON dosyasına kaydet"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"JSON kaydetme hatası: {e}") 