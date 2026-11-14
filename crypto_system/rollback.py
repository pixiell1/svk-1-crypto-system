from pathlib import Path
from core.updater import SafeUpdater

def find_project_dir():
    current = Path.cwd()
    if (current / "main.py").exists():
        return current
    for subdir in current.iterdir():
        if subdir.is_dir() and (subdir / "main.py").exists():
            return subdir
    raise FileNotFoundError("Не удалось найти папку с main.py")

def run_rollback():
    target = find_project_dir()
    print(f"Папка проекта найдена: {target}")
    
    updater = SafeUpdater(str(target))
    print("=== ЗАПУСК ОТКАТА ===")
    if updater.rollback():
        print(f"✅ Откат выполнен в {target}")
    else:
        print("❌ Ошибка отката")

if __name__ == "__main__":
    run_rollback()