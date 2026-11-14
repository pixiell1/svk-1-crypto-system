import json
import os
import hashlib
import time

USERS_FILE = "users.json"
MAX_ATTEMPTS = 3
BLOCK_TIME_SECONDS = 300

class UserManager:
    def __init__(self):
        self._users = {}
        self._security = {}
        self._load()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _load(self):
        if not os.path.exists(USERS_FILE):
            self._set_default()
            return

        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Проверяем, что это новый формат (с ключами "users" и "security")
            if "users" in data:
                self._users = data.get("users", {})
                self._security = data.get("security", {})
                
                # Если admin каким-то образом пропал, добавляем его
                if "admin" not in self._users:
                    self._users["admin"] = {
                        "password_hash": self._hash_password("admin123"),
                        "role": "admin"
                    }
                    self._save()
            else:
                # Это старый формат (просто словарь пользователей) — конвертируем
                print("⚠️ Обнаружен старый формат users.json. Конвертация...")
                self._users = data
                self._security = {}
                self._save()

        except Exception as e:
            print(f"Ошибка чтения users.json: {e}. Создаем дефолтный.")
            self._set_default()

    def _set_default(self):
        self._users = {
            "admin": {
                "password_hash": self._hash_password("admin123"),
                "role": "admin"
            }
        }
        self._security = {}
        self._save()

    def _save(self):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "users": self._users,
                "security": self._security
            }, f, indent=4, ensure_ascii=False)

    def check_block(self, username: str) -> tuple[bool, int]:
        if username not in self._security:
            return False, 0
        sec = self._security[username]
        blocked_until = sec.get("blocked_until", 0)
        now = time.time()
        if now < blocked_until:
            return True, int(blocked_until - now)
        if blocked_until > 0:
            sec["blocked_until"] = 0
            sec["attempts"] = 0
            self._save()
        return False, 0

    def authenticate(self, username: str, password: str) -> bool:
        is_blocked, _ = self.check_block(username)
        if is_blocked:
            return False

        user = self._users.get(username)
        if not user:
            self._register_fail(username)
            return False
        
        # Если хэш совпадает
        if user["password_hash"] == self._hash_password(password):
            if username in self._security:
                self._security[username]["attempts"] = 0
                self._save()
            return True
        else:
            self._register_fail(username)
            return False

    def _register_fail(self, username: str):
        if username not in self._security:
            self._security[username] = {"attempts": 0, "blocked_until": 0}
        sec = self._security[username]
        sec["attempts"] += 1
        if sec["attempts"] >= MAX_ATTEMPTS:
            sec["blocked_until"] = time.time() + BLOCK_TIME_SECONDS
        self._save()

    def get_role(self, username: str) -> str:
        return self._users.get(username, {}).get("role", "user")
    
    def get_attempts_left(self, username: str) -> int:
        if username not in self._security:
            return MAX_ATTEMPTS
        return MAX_ATTEMPTS - self._security[username].get("attempts", 0)