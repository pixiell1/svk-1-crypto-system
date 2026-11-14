import sys
import os
from pathlib import Path

def get_base_path() -> Path:
    """
    Возвращает папку, где находятся файлы программы.
    Если это .exe (PyInstaller) — папку рядом с .exe.
    Если это скрипт — папку, где лежит скрипт.
    """
    if getattr(sys, 'frozen', False):
        # Мы в собранном .exe
        return Path(sys.executable).parent
    else:
        # Мы в режиме разработки
        return Path(__file__).parent.parent