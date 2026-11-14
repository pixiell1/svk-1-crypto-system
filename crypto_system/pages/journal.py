from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QPushButton, QMessageBox
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from theme import T

class JournalPage(QWidget):
    def __init__(self, audit):
        super().__init__()
        self._audit = audit

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(16)

        title = QLabel("📋  Журнал событий")
        title.setStyleSheet("font-size: 26px; font-weight: 700; color: #ffffff;")
        v.addWidget(title)

        card = QFrame()
        card.setObjectName("Card")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(16, 16, 16, 16)

        # Таблица
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Время", "Событие", "Пользователь", "Результат"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        cv.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("🗑 Очистить журнал")
        self.clear_btn.setObjectName("Ghost")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet(f"color: {T.RED}; border: 1px solid {T.RED};")
        self.clear_btn.clicked.connect(self._clear_logs)
        btn_layout.addWidget(self.clear_btn)
        
        btn_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.setObjectName("Ghost")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh)
        btn_layout.addWidget(self.refresh_btn)

        cv.addLayout(btn_layout)

        v.addWidget(card)
        self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        if not self._audit:
            return

        records = self._audit.read_records(limit=200)
        # Разворачиваем, чтобы новые были сверху
        records = records[::-1]

        for r in records:
            row = self.table.rowCount()
            self.table.insertRow(row)

            ts = r.get("event_datetime", "")[:19]
            desc = r.get("description", "")
            user = r.get("user_account", "")
            status = r.get("status", "")
            action = r.get("action", "")
            level = r.get("level", "")

            self.table.setItem(row, 0, QTableWidgetItem(ts))
            self.table.setItem(row, 1, QTableWidgetItem(desc))
            self.table.setItem(row, 2, QTableWidgetItem(user))

            res_text, color = self._colorize(status, action, level)
            item = QTableWidgetItem(res_text)
            item.setForeground(QColor(color))
            self.table.setItem(row, 3, item)

    def _clear_logs(self):
        """Удаляет все записи из журнала"""
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "Журнал", "Журнал уже пуст.")
            return

        reply = QMessageBox.question(
            self, "Очистка журнала",
            "Вы уверены, что хотите удалить ВСЕ записи из журнала?\nЭто действие необратимо.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self._audit and self._audit.clear_log():
                self.refresh()
                # Записываем в лог факт очистки
                if self._audit:
                    # ИМПОРТИРУЕМ ПРАВИЛЬНЫЕ КЛАССЫ (если их нет в шапке файла, добавь)
                    from core.audit import EventCategory, EventStatus
                    
                    self._audit.log(
                        source="journal", user="admin",
                        description="Журнал событий очищен администратором",
                        category=EventCategory.OBJECT,  # <-- ИСПОЛЬЗУЕМ ENUM
                        status=EventStatus.SUCCESS      # <-- ИСПОЛЬЗУЕМ ENUM
                    )
                QMessageBox.information(self, "Успех", "Журнал очищен.")
                self.refresh()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось очистить журнал.")

    @staticmethod
    def _colorize(status, action, level):
        if level == "critical":
            return "● Критично", T.RED
        if status == "success":
            return "● Успешно", T.GREEN
        if status == "failure":
            return "● Неудачно", T.RED
        if action == "modify":
            return "● Изменение", T.YELLOW
        if action == "delete":
            return "● Удаление", T.ORANGE
        return "● Инфо", T.BLUE