import json
import os
from pathlib import Path
from core.updater import SafeUpdater

def find_project_dir():
    """Ищет папку, в которой лежит main.py"""
    current = Path.cwd()
    if (current / "main.py").exists():
        return current
    for subdir in current.iterdir():
        if subdir.is_dir() and (subdir / "main.py").exists():
            return subdir
    raise FileNotFoundError("Не удалось найти папку с main.py")

def run_update():
    target = find_project_dir()
    print(f"Папка проекта найдена: {target}")
    
    updater = SafeUpdater(str(target))
    
    new_version = {"major": 2, "minor": 0, "patch": 0, "build_date": "2025-05-10 18:00:00"}
    new_theme = {"app_name": "СВК-1 PRO", "accent_color": "#ff5722"}

    new_files = {
        "version.json": json.dumps(new_version, indent=2).encode("utf-8"),
        "ui_theme.json": json.dumps(new_theme, indent=2).encode("utf-8")
    }

    print("=== ЗАПУСК ОБНОВЛЕНИЯ ===")
    if updater.apply_update(new_files):
        print(f"✅ Обновление применено в {target}")
    else:
        print("❌ Ошибка обновления")

if __name__ == "__main__":
    run_update()