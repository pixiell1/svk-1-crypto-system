from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
)
from PySide6.QtCore import Qt
from theme import T

class Sidebar(QFrame):
    NAV_ITEMS = [
        ("home",    "🏠", "Главная"),
        ("keygen",  "🔑", "Генерация ключей"),
        ("keys",    "🗝", "Ключи"),
        ("journal", "📋", "Журнал событий"),
        ("settings","⚙",  "Настройки"),
    ]

    # ДОБАВЛЯЕМ АРГУМЕНТ version_string
    def __init__(self, on_nav, version_string="1.0.0"):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(240)
        self._on_nav = on_nav
        self._buttons = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Логотип
        logo = QFrame()
        logo.setFixedHeight(72)
        logo.setStyleSheet(f"border-bottom: 1px solid {T.BORDER};")
        logo_layout = QHBoxLayout(logo)
        logo_layout.setContentsMargins(20, 0, 20, 0)
        logo_layout.setSpacing(12)

        shield = QLabel("🛡")
        shield.setStyleSheet(f"font-size: 24px; color: {T.ACCENT};")

        title = QLabel("СВК-1")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #ffffff;")

        logo_layout.addWidget(shield)
        logo_layout.addWidget(title)
        logo_layout.addStretch()
        layout.addWidget(logo)

        # Навигация
        for key, icon, text in self.NAV_ITEMS:
            btn = QPushButton(f"  {icon}   {text}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._on_nav(k))
            layout.addWidget(btn)
            self._buttons[key] = btn

        layout.addStretch()

        # Статус снизу
        status = QFrame()
        status.setFixedHeight(80)
        status.setStyleSheet(f"border-top: 1px solid {T.BORDER};")
        s_layout = QVBoxLayout(status)
        s_layout.setContentsMargins(20, 14, 20, 14)
        s_layout.setSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(8)
        dot = QFrame()
        dot.setFixedSize(10, 10)
        dot.setObjectName("StatusDot")
        row.addWidget(dot)
        row.addWidget(QLabel("Система в порядке"))
        row.addStretch()
        s_layout.addLayout(row)

        # ВЫВОДИМ ПЕРЕДАННУЮ ВЕРСИЮ
        self.ver_label = QLabel(f"Версия {version_string}")
        self.ver_label.setObjectName("StatusSub")
        s_layout.addWidget(self.ver_label)

        layout.addWidget(status)

    def select(self, key: str):
        for k, btn in self._buttons.items():
            btn.setChecked(k == key)