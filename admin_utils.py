from datetime import datetime, timedelta
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Sabitler
ADMIN_ID = "Cepyseo"  # Admin kullanıcı adı
ADMIN_DATA_DIR = Path("admin_data")
USER_CREDITS_DIR = Path("user_credits")
PREMIUM_USERS_FILE = ADMIN_DATA_DIR / "premium_users.json"
BANNED_USERS_FILE = ADMIN_DATA_DIR / "banned_users.json"

# Dizinleri oluştur
ADMIN_DATA_DIR.mkdir(exist_ok=True)
USER_CREDITS_DIR.mkdir(exist_ok=True)

class UserManager:
    def __init__(self):
        self.premium_users = self._load_json(PREMIUM_USERS_FILE, {})
        self.banned_users = self._load_json(BANNED_USERS_FILE, {})

    def _load_json(self, file_path: Path, default_value: dict) -> dict:
        if file_path.exists():
            try:
                return json.loads(file_path.read_text())
            except Exception as e:
                logger.error(f"JSON yükleme hatası {file_path}: {e}")
        return default_value

    def _save_json(self, file_path: Path, data: dict):
        try:
            file_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"JSON kaydetme hatası {file_path}: {e}")

    def is_admin(self, username: str) -> bool:
        """Kullanıcının admin olup olmadığını kontrol et"""
        return username == ADMIN_ID

    def is_premium(self, user_id: int) -> bool:
        """Kullanıcının premium olup olmadığını kontrol et"""
        user_id = str(user_id)
        if user_id in self.premium_users:
            expiry = datetime.fromisoformat(self.premium_users[user_id])
            return expiry > datetime.now()
        return False

    def is_banned(self, user_id: int) -> bool:
        """Kullanıcının yasaklı olup olmadığını kontrol et"""
        return str(user_id) in self.banned_users

    def add_premium(self, user_id: int, days: int = 30):
        """Kullanıcıya premium ver"""
        user_id = str(user_id)
        expiry = datetime.now() + timedelta(days=days)
        self.premium_users[user_id] = expiry.isoformat()
        self._save_json(PREMIUM_USERS_FILE, self.premium_users)

    def remove_premium(self, user_id: int):
        """Kullanıcının premium üyeliğini kaldır"""
        user_id = str(user_id)
        if user_id in self.premium_users:
            del self.premium_users[user_id]
            self._save_json(PREMIUM_USERS_FILE, self.premium_users)

    def ban_user(self, user_id: int, reason: str = ""):
        """Kullanıcıyı yasakla"""
        user_id = str(user_id)
        self.banned_users[user_id] = {
            "date": datetime.now().isoformat(),
            "reason": reason
        }
        self._save_json(BANNED_USERS_FILE, self.banned_users)

    def unban_user(self, user_id: int):
        """Kullanıcının yasağını kaldır"""
        user_id = str(user_id)
        if user_id in self.banned_users:
            del self.banned_users[user_id]
            self._save_json(BANNED_USERS_FILE, self.banned_users)

class UserCredits:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.credits_file = USER_CREDITS_DIR / f"{user_id}.json"
        self.credits = self._load_credits()

    def _load_credits(self) -> dict:
        if self.credits_file.exists():
            try:
                data = json.loads(self.credits_file.read_text())
                # Günlük kredileri kontrol et ve sıfırla
                last_reset = datetime.fromisoformat(data.get('last_reset', '2000-01-01'))
                if last_reset.date() < datetime.now().date():
                    return self._reset_credits()
                return data
            except Exception as e:
                logger.error(f"Kredi yükleme hatası: {e}")
        return self._reset_credits()

    def _reset_credits(self) -> dict:
        """Günlük kredileri sıfırla"""
        credits = {
            'ai_chat': 12,
            'image_search': 12,
            'file_operations': 5,
            'last_reset': datetime.now().isoformat()
        }
        self._save_credits(credits)
        return credits

    def _save_credits(self, credits: dict):
        try:
            self.credits_file.write_text(json.dumps(credits, indent=2))
        except Exception as e:
            logger.error(f"Kredi kaydetme hatası: {e}")

    def check_credits(self, feature: str) -> bool:
        """Kredi kontrolü yap"""
        if feature not in self.credits:
            return False
        return self.credits[feature] > 0

    def use_credit(self, feature: str) -> bool:
        """Kredi kullan"""
        if not self.check_credits(feature):
            return False
        self.credits[feature] -= 1
        self._save_credits(self.credits)
        return True

    def get_credits(self) -> dict:
        """Kalan kredileri göster"""
        return {k: v for k, v in self.credits.items() if k != 'last_reset'} 