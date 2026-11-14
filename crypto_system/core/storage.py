import json
import os
from datetime import datetime

KEYS_FILE = "keys.json"

class KeyStorage:
    def __init__(self):
        self._keys = []

    def _load(self):
        """Всегда перечитывает файл с диска"""
        if os.path.exists(KEYS_FILE):
            try:
                with open(KEYS_FILE, "r", encoding="utf-8") as f:
                    self._keys = json.load(f)
            except Exception:
                self._keys = []
        else:
            self._keys = []

    def _save(self):
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._keys, f, indent=4, ensure_ascii=False)

    def add_key(self, key_hex: str, size_bits: int, algo: str):
        self._load() # <--- Перечитываем перед добавлением
        # Генерируем уникальный ID (максимальный + 1)
        new_id = max([k["id"] for k in self._keys], default=0) + 1
        record = {
            "id": new_id,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "size": f"{size_bits} бит",
            "algo": algo,
            "key_hex": key_hex[:16] + "...",
            "status": "Активен"
        }
        self._keys.append(record)
        self._save()

    def get_all(self) -> list:
        self._load() # <--- Перечитываем перед выдачей
        return self._keys

    def delete_key(self, key_id: int):
        self._load() # <--- Перечитываем перед удалением
        self._keys = [k for k in self._keys if k["id"] != key_id]
        self._save()

    def clear_all(self):
        self._keys = []
        self._save()