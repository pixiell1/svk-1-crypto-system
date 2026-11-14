from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from theme import T
from core.storage import KeyStorage
from core.audit import EventCategory, EventAction, EventStatus, EventLevel

class KeysPage(QWidget):
    def __init__(self, audit):
        super().__init__()
        self._audit = audit
        self._storage = KeyStorage()

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(20)

        v.addWidget(QLabel("🗝  Хранилище ключей", styleSheet="font-size: 26px; font-weight: 700; color: #ffffff;"))

        card = QFrame()
        card.setObjectName("Card")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(20, 20, 20, 20)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Дата", "Алгоритм", "Размер", "Ключ"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        cv.addWidget(self.table)

        btn_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("🗑 Удалить все ключи")
        self.clear_btn.setObjectName("Ghost")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet(f"color: {T.RED}; border: 1px solid {T.RED};")
        self.clear_btn.clicked.connect(self._clear_all_keys)
        btn_layout.addWidget(self.clear_btn)

        btn_layout.addStretch()
        
        self.del_btn = QPushButton("Удалить выбранный")
        self.del_btn.setObjectName("Ghost")
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.clicked.connect(self._delete_key)
        btn_layout.addWidget(self.del_btn)
        
        cv.addLayout(btn_layout)
        v.addWidget(card)
        
        self.refresh() # Первичная загрузка

    def refresh(self):
        """Загружает данные из файла и обновляет таблицу"""
        self.table.setRowCount(0)
        keys = self._storage.get_all() # Берет данные с диска
        
        if not keys:
            self.table.insertRow(0)
            item = QTableWidgetItem("Нет сгенерированных ключей")
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(0, 0, item)
            self.table.setSpan(0, 0, 1, 5)
            return

        for k in keys:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(k.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(k.get("datetime", "")))
            self.table.setItem(row, 2, QTableWidgetItem(k.get("algo", "")))
            self.table.setItem(row, 3, QTableWidgetItem(k.get("size", "")))
            self.table.setItem(row, 4, QTableWidgetItem(k.get("key_hex", "")))

    def _delete_key(self):
        row = self.table.currentRow()
        if row < 0 or self.table.rowCount() == 0 or self.table.item(row, 0).text() == "Нет сгенерированных ключей":
            QMessageBox.warning(self, "Внимание", "Выберите ключ для удаления")
            return
        
        key_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(self, "Удаление", f"Удалить ключ ID {key_id}? Это действие необратимо.", QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self._storage.delete_key(key_id) # Удаляет из файла
            self.refresh() # Обновляет таблицу
            
            if self._audit:
                self._audit.log("keys", "admin", f"Удаление ключа ID {key_id}", EventCategory.OBJECT, action=EventAction.DELETE, status=EventStatus.SUCCESS)

    def _clear_all_keys(self):
        if self.table.rowCount() == 0 or self.table.item(0, 0).text() == "Нет сгенерированных ключей":
            return
            
        reply = QMessageBox.question(self, "Очистка хранилища", "Вы уверены, что хотите удалить ВСЕ ключи?\nЭто действие необратимо.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self._storage.clear_all() # Очищает файл
            self.refresh() # Обновляет таблицу
            
            if self._audit:
                self._audit.log(
                    source="keys", user="admin", 
                    description="Полная очистка хранилища ключей", 
                    category=EventCategory.OBJECT, 
                    action=EventAction.DELETE, 
                    status=EventStatus.SUCCESS,
                    level=EventLevel.WARNING
                )