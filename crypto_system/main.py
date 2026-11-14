import sys
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget
)

from core.fingerprint import SystemFingerprint
from core.app_meta import AppMeta
from theme import apply_theme, T
from widgets.sidebar import Sidebar
from widgets.topbar import TopBar
from auth_dialog import AuthDialog

from pages.home import HomePage
from pages.keygen import KeyGenPage
from pages.keys import KeysPage
from pages.journal import JournalPage
from pages.settings import SettingsPage

from core.audit import Audit, LogFormat, EventCategory, EventStatus, EventLevel
from core.config import ConfigLoader


class MainWindow(QMainWindow):
    def __init__(self, current_user: str, meta: AppMeta):
        super().__init__()
        self._meta = meta
        
        # Заголовок окна с версией
        self.setWindowTitle(f"{self._meta.app_name} v{self._meta.version_string} — Средство выработки ключей")
        self.resize(1440, 900)

        # ==============================================================
        # КОНФИГ И АУДИТ
        # ==============================================================
        self._config_loader = ConfigLoader("config.json")
        self._cfg = None
        try:
            self._cfg = self._config_loader.load()
        except Exception as e:
            print(f"[Main] Ошибка загрузки config.json: {e}")

        try:
            log_path = "logs/security.log"
            log_fmt = LogFormat.JSON
            max_size = 100
            cleanup_days = 30

            if self._cfg:
                log_path = self._cfg.logging.log_path
                log_fmt = LogFormat(self._cfg.logging.log_format)
                max_size = int(''.join(filter(str.isdigit, self._cfg.logging.max_file_size)) or 100)
                cleanup_days = int(''.join(filter(str.isdigit, self._cfg.logging.cleanup_period)) or 30)

            os.makedirs(os.path.dirname(log_path), exist_ok=True)

            self._audit = Audit(
                log_path=log_path,
                log_format=log_fmt,
                max_file_size_mb=max_size,
                cleanup_period_days=cleanup_days,
            )
        except Exception as e:
            print(f"[Main] ОШИБКА АУДИТА: {e}")
            self._audit = None

        self._fp = SystemFingerprint().get_fingerprint()

        # ==============================================================
        # ИНТЕРФЕЙС
        # ==============================================================
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ПЕРЕДАЕМ ВЕРСИЮ В САЙДБАР
        self.sidebar = Sidebar(on_nav=self._navigate, version_string=self._meta.version_string)
        root.addWidget(self.sidebar)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        self.topbar = TopBar(current_user=current_user, on_login_click=self._open_auth)
        right.addWidget(self.topbar)

        self.stack = QStackedWidget()
        
        self.home_page = HomePage(
            events_provider=self._load_events, 
            navigate_callback=self._navigate,
            fingerprint=self._fp
        )
        self.keygen_page = KeyGenPage(audit=self._audit, on_generate=self._on_generate)
        self.keys_page = KeysPage(audit=self._audit)
        self.journal_page = JournalPage(audit=self._audit)
        
        cfg_to_pass = self._cfg if self._cfg else ConfigLoader.create_default()
        self.settings_page = SettingsPage(
            config_loader=self._config_loader,
            current_cfg=cfg_to_pass,
            audit=self._audit
        )

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.keygen_page)
        self.stack.addWidget(self.keys_page)
        self.stack.addWidget(self.journal_page)
        self.stack.addWidget(self.settings_page)
        right.addWidget(self.stack)

        right_widget = QWidget()
        right_widget.setLayout(right)
        root.addWidget(right_widget)

        self._navigate("home")

        # СТАТУСБАР УБРАН (ничего не вызываем)

    def _navigate(self, key: str):
        pages = {"home": 0, "keygen": 1, "keys": 2, "journal": 3, "settings": 4}
        self.stack.setCurrentIndex(pages.get(key, 0))
        self.sidebar.select(key)
        
        if key == "journal":
            self.journal_page.refresh()
        elif key == "home":
            self.home_page.refresh_events()
        elif key == "keys":
            self.keys_page.refresh()

    def _open_auth(self):
        dialog = AuthDialog(self._audit, self)
        if dialog.exec() == AuthDialog.Accepted:
            new_user = dialog.get_username()
            self.topbar.set_user(new_user)
            self.home_page.refresh_events()
            if self.stack.currentIndex() == 3:
                self.journal_page.refresh()

    def _load_events(self):
        if not self._audit:
            return []
        try:
            records = self._audit.read_records(limit=20)
            records = records[::-1]
            return [
                (r.get("event_datetime", "")[:19], r.get("description", ""),
                 r.get("user_account", ""), r.get("status", "success") or "success")
                for r in records
            ]
        except Exception as e:
            print(f"Ошибка чтения логов: {e}")
            return []

    def _on_generate(self):
        self.home_page.refresh_events()
        self.keys_page.refresh() 
        if self.stack.currentIndex() == 3:
            self.journal_page.refresh()


# ======================================================================
# ТОЧКА ВХОДА
# ======================================================================
def main():
    app = QApplication(sys.argv)
    
    # 1. ЧИТАЕМ МЕТАДАННЫЕ
    meta = AppMeta()
    print(f"=== ЗАПУСК: Версия {meta.version_string}, Цвет {meta.accent_color} ===")
    
    # 2. ПРИМЕНЯЕМ ТЕМУ
    T.ACCENT = meta.accent_color
    apply_theme(app)

    # 3. АУДИТ
    config_loader = ConfigLoader("config.json")
    try:
        cfg = config_loader.load()
    except Exception:
        cfg = ConfigLoader.create_default()

    try:
        os.makedirs(os.path.dirname(cfg.logging.log_path), exist_ok=True)
        audit = Audit(
            log_path=cfg.logging.log_path,
            log_format=LogFormat(cfg.logging.log_format),
            max_file_size_mb=int(''.join(filter(str.isdigit, cfg.logging.max_file_size)) or 100),
            cleanup_period_days=int(''.join(filter(str.isdigit, cfg.logging.cleanup_period)) or 30),
        )
    except Exception as e:
        print(f"Не удалось создать аудит: {e}")
        audit = None

    # 4. ЛОГИРУЕМ ЗАПУСК
    fp = SystemFingerprint().get_fingerprint()
    if audit:
        audit.log(
            source="system", user="system",
            description=f"Запуск программы v{meta.version_string}. Отпечаток: {fp}",
            category=EventCategory.AUTH,
            status=EventStatus.SUCCESS,
            level=EventLevel.INFO
        )

    # 5. АВТОРИЗАЦИЯ
    auth = AuthDialog(audit)
    if auth.exec() != AuthDialog.Accepted:
        sys.exit(0)

    username = auth.get_username()

    # 6. ЗАПУСК ОКНА
    win = MainWindow(current_user=username, meta=meta)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()