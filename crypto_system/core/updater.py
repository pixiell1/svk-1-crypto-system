import os
import shutil
from pathlib import Path

class SafeUpdater:
    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir).resolve()
        self.backup_dir = self.target_dir / "_backup"
        self.tmp_dir = self.target_dir / "_tmp_update"

    def apply_update(self, new_files: dict) -> bool:
        try:
            # 1. Очистка временных папок от прошлых запусков
            if self.tmp_dir.exists():
                shutil.rmtree(self.tmp_dir)
            self.tmp_dir.mkdir(parents=True)
            
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            self.backup_dir.mkdir(parents=True)

            # 2. Записываем новые файлы во временную папку
            for rel_path, content in new_files.items():
                dst = self.tmp_dir / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                with open(dst, "wb") as f:
                    f.write(content)

            # 3. Делаем бэкап старых файлов
            for rel_path in new_files.keys():
                old = self.target_dir / rel_path
                if old.exists():
                    bak = self.backup_dir / rel_path
                    bak.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(old, bak)

            # 4. Заменяем файлы
            for rel_path in new_files.keys():
                dst = self.target_dir / rel_path
                if dst.exists():
                    dst.unlink()
                shutil.copy2(self.tmp_dir / rel_path, dst)

            # 5. Удаляем временную папку
            shutil.rmtree(self.tmp_dir)
            print("✅ Обновление успешно применено.")
            return True

        except Exception as e:
            print(f"❌ Ошибка при обновлении: {e}")
            self.rollback()
            return False

    def rollback(self) -> bool:
        if not self.backup_dir.exists():
            print("⚠️ Бэкап не найден.")
            return False

        try:
            for root, _, files in os.walk(self.backup_dir):
                for name in files:
                    src = Path(root) / name
                    rel = src.relative_to(self.backup_dir)
                    dst = self.target_dir / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            print("✅ Откат успешно выполнен.")
            return True
        except Exception as e:
            print(f"❌ Ошибка отката: {e}")
            return False