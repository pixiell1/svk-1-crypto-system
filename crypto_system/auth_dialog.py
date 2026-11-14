from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt
from theme import T
from core.audit import EventCategory, EventStatus, EventLevel
from core.users import UserManager

class AuthDialog(QDialog):
    def __init__(self, audit, parent=None):
        super().__init__(parent)
        self._audit = audit
        self._user_manager = UserManager()
        self._username = None

        self.setWindowTitle("Вход в систему")
        self.setFixedSize(350, 240)
        self.setStyleSheet(f"background-color: {T.BG_CARD}; color: {T.TEXT};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("🛡 Авторизация в СВК-1")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин")
        self.login_input.setStyleSheet(f"padding: 8px; border: 1px solid {T.BORDER}; border-radius: 4px; background: {T.BG};")
        layout.addWidget(self.login_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Пароль")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setStyleSheet(f"padding: 8px; border: 1px solid {T.BORDER}; border-radius: 4px; background: {T.BG};")
        layout.addWidget(self.pass_input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.login_btn = QPushButton("Войти")
        self.login_btn.setObjectName("Primary")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self._try_login)
        btn_layout.addWidget(self.login_btn)
        layout.addLayout(btn_layout)

    def _try_login(self):
        user = self.login_input.text().strip()
        pwd = self.pass_input.text().strip()

        # 1. Проверяем, не заблокирован ли пользователь
        is_blocked, seconds_left = self._user_manager.check_block(user)
        if is_blocked:
            mins = seconds_left // 60
            secs = seconds_left % 60
            QMessageBox.critical(self, "Заблокировано", 
                f"Превышено количество попыток.\nПопробуйте через {mins} мин. {secs} сек.")
            
            # Логируем попытку входа в заблокированный аккаунт
            if self._audit:
                self._audit.log(
                    source="auth_module", user=user, 
                    description="Попытка входа в заблокированный аккаунт", 
                    category=EventCategory.AUTH, 
                    status=EventStatus.FAILURE,
                    level=EventLevel.WARNING
                )
            return

        # 2. Проверяем пароль
        if self._user_manager.authenticate(user, pwd):
            self._username = user
            
            if self._audit:
                self._audit.log(
                    source="auth_module", user=user, 
                    description=f"Вход в систему (роль: {self._user_manager.get_role(user)})", 
                    category=EventCategory.AUTH, 
                    status=EventStatus.SUCCESS,
                    level=EventLevel.INFO
                )
            self.accept()
        else:
            # 3. Неудачная попытка
            attempts_left = self._user_manager.get_attempts_left(user)
            
            if self._audit:
                self._audit.log(
                    source="auth_module", user=user if user else "Неизвестно", 
                    description="Неуспешная аутентификация (неверный пароль)", 
                    category=EventCategory.AUTH, 
                    status=EventStatus.FAILURE,
                    level=EventLevel.WARNING
                )
            
            if attempts_left <= 0:
                QMessageBox.critical(self, "Блокировка", "Вы превысили лимит попыток. Аккаунт заблокирован на 5 минут.")
            else:
                QMessageBox.warning(self, "Ошибка", f"Неверный логин или пароль!\nОсталось попыток: {attempts_left}")
            
            self.pass_input.clear()

    def get_username(self) -> str:
        return self._username