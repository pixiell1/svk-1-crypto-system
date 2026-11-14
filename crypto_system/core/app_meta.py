from pathlib import Path
import json

class AppMeta:
    def __init__(self):
        # Определяем базовую директорию (где лежат файлы)
        self._base = self._find_base_dir()
        
        # Значения по умолчанию (если файлов нет)
        self._version = {"major": 1, "minor": 0, "patch": 0, "build_date": "unknown"}
        self._theme = {"app_name": "СВК-1", "accent_color": "#22d3ee"}
        
        self._load()

    def _find_base_dir(self) -> Path:
        """
        Ищет папку, в которой реально лежат файлы.
        Если запущен .exe (PyInstaller) — папку рядом с .exe.
        Если скрипт — корень проекта (на уровень выше папки core).
        """
        import sys
        # Если это скомпилированный .exe
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent.resolve()
        
        # Если запущен скрипт: app_meta.py лежит в core/, значит корень на уровень выше
        current_file = Path(__file__).resolve()
        return current_file.parent.parent

    def _load(self):
        """Читает файлы version.json и ui_theme.json"""
        v_path = self._base / "version.json"
        if v_path.exists():
            try:
                with open(v_path, "r", encoding="utf-8") as f:
                    self._version = json.load(f)
            except Exception as e:
                print(f"[AppMeta] Ошибка чтения version.json: {e}")
        
        t_path = self._base / "ui_theme.json"
        if t_path.exists():
            try:
                with open(t_path, "r", encoding="utf-8") as f:
                    self._theme = json.load(f)
            except Exception as e:
                print(f"[AppMeta] Ошибка чтения ui_theme.json: {e}")

    @property
    def version_string(self) -> str:
        v = self._version
        return f"{v.get('major', 1)}.{v.get('minor', 0)}.{v.get('patch', 0)}"

    @property
    def build_date(self) -> str:
        return self._version.get("build_date", "unknown")

    @property
    def app_name(self) -> str:
        return self._theme.get("app_name", "СВК-1")

    @property
    def accent_color(self) -> str:
        return self._theme.get("accent_color", "#22d3ee")

    @property
    def base_dir(self) -> Path:
        """Возвращает путь к корневой папке (полезно для отладки)"""
        return self._base