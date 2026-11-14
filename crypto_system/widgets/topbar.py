from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLabel, QApplication
from PySide6.QtCore import Qt
from theme import T

class TopBar(QFrame):
    # Изменили имя аргумента на current_user
    def __init__(self, current_user="Гость", on_login_click=None):
        super().__init__()
        self.setObjectName("TopBar")
        self.setFixedHeight(60)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        title = QLabel("Средство выработки личного и открытого ключей")
        title.setObjectName("AppSubtitle")
        layout.addWidget(title)
        layout.addStretch()

        # Кнопка входа (сразу показываем имя пользователя)
        self.login_btn = QPushButton(f"👤 {current_user}")
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {T.ACCENT};
                border: 1px solid {T.ACCENT_DIM};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {T.BG_CARD_HOV};
            }}
        """)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        
        if on_login_click:
            self.login_btn.clicked.connect(on_login_click)
            
        layout.addWidget(self.login_btn)

        # Системные кнопки (свернуть, развернуть, закрыть)
        for symbol in ("⚙", "—", "▢", "✕"):
            b = QPushButton(symbol)
            b.setFixedSize(32, 32)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none;
                    color: {T.TEXT_MUTED}; font-size: 14px;
                }}
                QPushButton:hover {{
                    background: {T.BG_CARD}; color: {T.TEXT};
                    border-radius: 4px;
                }}
            """)
            if symbol == "✕":
                b.clicked.connect(QApplication.quit)
            layout.addWidget(b)

    def set_user(self, username: str):
        """Обновляет имя пользователя в кнопке"""
        if username:
            self.login_btn.setText(f"👤 {username}")
            self.login_btn.setStyleSheet(f"color: {T.GREEN}; border: none; font-weight: bold;")
        else:
            self.login_btn.setText("👤 Войти в систему")