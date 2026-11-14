from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from theme import T
from widgets.common import make_separator, make_mini_title, make_kv_row


class ClickableCard(QFrame):
    def __init__(self, icon, title, text, color, parent_page, target_key):
        super().__init__()
        self.setObjectName("Card")
        self.setMinimumHeight(170)
        self.setCursor(Qt.PointingHandCursor)
        self._parent_page = parent_page
        self._target_key = target_key

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(10)

        ic = QLabel(icon)
        ic.setStyleSheet(f"font-size: 26px; color: {color};")
        v.addWidget(ic)

        t = QLabel(title)
        t.setObjectName("CardTitle")
        v.addWidget(t)

        d = QLabel(text)
        d.setObjectName("CardText")
        d.setWordWrap(True)
        v.addWidget(d)
        v.addStretch()

        arrow = QLabel("→")
        arrow.setStyleSheet(f"color: {T.ACCENT}; font-size: 18px;")
        arrow.setAlignment(Qt.AlignRight)
        v.addWidget(arrow)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._parent_page.navigate_to(self._target_key)
        super().mousePressEvent(event)


class HomePage(QWidget):
    def __init__(self, events_provider=None, navigate_callback=None, fingerprint=""):
        super().__init__()
        self._events_provider = events_provider
        self._navigate_callback = navigate_callback
        self._fingerprint = fingerprint
        self.table = None

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        layout.addWidget(self._build_hero())
        layout.addLayout(self._build_cards())

        bottom = QHBoxLayout()
        bottom.setSpacing(20)
        bottom.addWidget(self._build_events(), stretch=2)
        bottom.addWidget(self._build_status(), stretch=1)
        layout.addLayout(bottom)

    def navigate_to(self, key):
        if self._navigate_callback:
            self._navigate_callback(key)

    def _build_hero(self) -> QFrame:
        hero = QFrame()
        hero.setObjectName("Hero")
        hero.setFixedHeight(170)
        h = QHBoxLayout(hero)
        h.setContentsMargins(32, 24, 32, 24)
        left = QVBoxLayout()
        left.setSpacing(6)

        title = QLabel("СВК-1")
        title.setObjectName("HeroTitle")
        left.addWidget(title)
        sub = QLabel("Программное средство криптографической защиты информации")
        sub.setObjectName("HeroSubtitle")
        left.addWidget(sub)
        meta = QLabel("Соответствует СТБ 34.101.27 (уровень 2)")
        meta.setObjectName("HeroMeta")
        left.addWidget(meta)
        left.addStretch()
        h.addLayout(left)
        h.addStretch()
        icon = QLabel("🔒")
        icon.setStyleSheet(f"font-size: 90px; color: {T.ACCENT};")
        h.addWidget(icon)
        return hero

    def _build_cards(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)
        cards = [
            ("🔑", "Генерация ключей", "Создание личного и открытого ключей на основе криптографически стойкого ГСЧ.", T.ACCENT, "keygen"),
            ("🛡", "Защита ключей", "Безопасное хранение личного ключа, контроль операций, разграничение доступа.", T.GREEN, "keys"),
            ("👤", "Управление доступом", "Аутентификация, разграничение ролей, контроль качества пароля.", T.ACCENT, "settings"),
            ("📋", "Журнал событий", "Логирование всех криптографических операций и действий пользователей.", T.BLUE, "journal"),
        ]
        for icon, title, text, color, key in cards:
            row.addWidget(ClickableCard(icon, title, text, color, self, key))
        return row

    def _build_events(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(12)

        title = QLabel("Последние события")
        title.setObjectName("SectionTitle")
        v.addWidget(title)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Время", "Событие", "Пользователь", "Результат"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.refresh_events()
        v.addWidget(self.table)
        v.addStretch()

        footer = QHBoxLayout()
        footer.addStretch()
        all_btn = QPushButton("Все события →")
        all_btn.setObjectName("Ghost")
        all_btn.setCursor(Qt.PointingHandCursor)
        all_btn.clicked.connect(lambda: self.navigate_to("journal"))
        footer.addWidget(all_btn)
        v.addLayout(footer)
        return card

    def refresh_events(self):
        if not self.table:
            return
        self.table.setRowCount(0)
        events = self._events_provider() if self._events_provider else []
        if not events:
            events = [("—", "Нет событий", "—", "info")]
        for row in events[:6]:
            self._add_event_row(self.table, *row)
        height = min(260, 42 * (self.table.rowCount() + 1))
        self.table.setFixedHeight(height)

    def _add_event_row(self, table, time_str, event, user, result):
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(time_str))
        table.setItem(row, 1, QTableWidgetItem(event))
        table.setItem(row, 2, QTableWidgetItem(user))
        res_map = {"success": ("● Успешно", T.GREEN), "failure": ("● Неудачно", T.RED), "info": ("● Инфо", T.BLUE)}
        text, color = res_map.get(result, ("", T.TEXT))
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color))
        table.setItem(row, 3, item)

    def _build_status(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(360)
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(14)

        v.addWidget(QLabel("Статус системы", objectName="SectionTitle"))
        ok = QLabel("✓ Работает")
        ok.setObjectName("StatusOk")
        v.addWidget(ok)
        v.addWidget(QLabel("Все модули функционируют корректно", objectName="StatusSub"))
        v.addWidget(make_separator())

        v.addWidget(make_mini_title("Информация о ключах"))
        v.addLayout(make_kv_row("🔑", "Личный ключ", "🔒 Защищён"))
        v.addLayout(make_kv_row("🗝", "Открытый ключ", "🔓 Доступен"))
        v.addWidget(make_separator())

        v.addWidget(make_mini_title("Системные параметры"))
        v.addLayout(make_kv_row("", "ОС", "Windows"))
        v.addLayout(make_kv_row("", "Отпечаток ПК", self._fingerprint[:16] + "..."))
        v.addLayout(make_kv_row("", "Криптобиблиотека", "СТБ 34.101.47"))
        v.addStretch()
        return card