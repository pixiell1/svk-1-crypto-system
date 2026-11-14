from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QFormLayout, QLineEdit, QComboBox, QPushButton, QMessageBox,
    QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt
from theme import T
from core.audit import EventCategory, EventAction, EventStatus, EventLevel
from core.integrity import IntegrityChecker
from core.sbom import SbomChecker
from core.paths import get_base_path
from core.fingerprint import SystemFingerprint
from PySide6.QtWidgets import QDialog, QDialogButtonBox


class SettingsPage(QWidget):

    def _show_fingerprint(self):
        fp = SystemFingerprint().get_fingerprint()
        details = SystemFingerprint().get_details()
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Отпечаток системы")
        msg.setIcon(QMessageBox.Information)
        
        info = f"<b>Ваш уникальный ID:</b><br>{fp}<br><br>"
        info += "<b>Детали:</b><br>"
        for k, v in details.items():
            info += f"{k}: {v}<br>"
        
        msg.setText(info)
        msg.exec()

    def __init__(self, config_loader, current_cfg, audit):
        super().__init__()
        self._loader = config_loader
        self._cfg = current_cfg
        self._audit = audit

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        v = QVBoxLayout(content)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(20)

        v.addWidget(QLabel("⚙  Настройки системы", styleSheet="font-size: 26px; font-weight: 700; color: #ffffff;"))

        # --- БЛОК 1: КОНФИГУРАЦИЯ ---
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        
        form = QFormLayout()
        form.setSpacing(15)

        form.addRow(QLabel("Параметры логирования", styleSheet=f"font-size: 16px; font-weight: bold; color: {T.ACCENT};"))

        self.path_input = QLineEdit(self._cfg.logging.log_path)
        form.addRow("Путь к файлу логов:", self.path_input)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["json", "csv", "cef"])
        self.format_combo.setCurrentText(self._cfg.logging.log_format)
        form.addRow("Формат логов:", self.format_combo)

        self.size_input = QLineEdit(self._cfg.logging.max_file_size)
        form.addRow("Макс. размер файла (MB):", self.size_input)

        self.cleanup_input = QLineEdit(self._cfg.logging.cleanup_period)
        form.addRow("Период очистки (дней):", self.cleanup_input)

        form.addRow(QLabel("Криптографические алгоритмы", styleSheet=f"font-size: 16px; font-weight: bold; color: {T.ACCENT}; margin-top: 15px;"))

        # ВЫПАДАЮЩИЕ СПИСКИ ВМЕСТО ТЕКСТОВЫХ ПОЛЕЙ
        self.enc_combo = QComboBox()
        self.enc_combo.addItems(["AES-256-GCM", "AES-128-CBC", "Кузнечик (СТБ 34.101.31)"])
        self.enc_combo.setCurrentText(self._cfg.crypto.encryption)
        form.addRow("Алгоритм шифрования:", self.enc_combo)

        self.hash_combo = QComboBox()
        self.hash_combo.addItems(["SHA-256", "SHA-512", "bash-hash (СТБ 34.101.31)"])
        self.hash_combo.setCurrentText(self._cfg.crypto.hashing)
        form.addRow("Алгоритм хэширования:", self.hash_combo)

        self.sig_combo = QComboBox()
        self.sig_combo.addItems(["ECDSA-P256", "Ed25519", "belt-ecdsa (СТБ 34.101.31)"])
        self.sig_combo.setCurrentText(self._cfg.crypto.digital_signature)
        form.addRow("Алгоритм ЭЦП:", self.sig_combo)

        card_layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("💾 Сохранить настройки")
        self.save_btn.setObjectName("Primary")
        self.save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.save_btn)
        card_layout.addLayout(btn_layout)
        v.addWidget(card)

        # --- БЛОК 2: ПРОВЕРКА ---
        update_card = QFrame()
        update_card.setObjectName("Card")
        uv = QVBoxLayout(update_card)
        uv.setContentsMargins(24, 24, 24, 24)
        uv.setSpacing(15)

        uv.addWidget(QLabel("Проверка целостности и обновлений", styleSheet=f"font-size: 16px; font-weight: bold; color: {T.ACCENT};"))
        
        self.check_btn = QPushButton("🔍 Проверить манифест и SBOM")
        self.check_btn.setObjectName("Primary")
        self.check_btn.clicked.connect(self._check_update)
        uv.addWidget(self.check_btn)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(150)
        uv.addWidget(self.log_area)

        v.addWidget(update_card)
        v.addStretch()

        fp_layout = QHBoxLayout()
        self.fp_btn = QPushButton("🖥 Показать отпечаток системы")
        self.fp_btn.setObjectName("Ghost")
        self.fp_btn.setCursor(Qt.PointingHandCursor)
        self.fp_btn.clicked.connect(self._show_fingerprint)
        fp_layout.addWidget(self.fp_btn)
        fp_layout.addStretch()
        card_layout.addLayout(fp_layout)

    def _save_settings(self):
        try:
            self._cfg.logging.log_path = self.path_input.text().strip()
            self._cfg.logging.log_format = self.format_combo.currentText()
            self._cfg.logging.max_file_size = f"{''.join(filter(str.isdigit, self.size_input.text()))}MB"
            self._cfg.logging.cleanup_period = f"{''.join(filter(str.isdigit, self.cleanup_input.text()))}d"
            
            # Берем данные из выпадающих списков
            self._cfg.crypto.encryption = self.enc_combo.currentText()
            self._cfg.crypto.hashing = self.hash_combo.currentText()
            self._cfg.crypto.digital_signature = self.sig_combo.currentText()

            self._loader.save(self._cfg)
            if self._audit:
                self._audit.log("settings", "admin", "Изменение конфигурации", EventCategory.ACCOUNT, action=EventAction.MODIFY, status=EventStatus.SUCCESS)
            QMessageBox.information(self, "Успех", "Настройки сохранены!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _check_update(self):
        self.log_area.clear()
        base_dir = get_base_path()
        
        # 1. SBOM
        sbom = SbomChecker(str(base_dir / "sbom.json"))
        if not sbom.load(): return self.log_area.append("❌ sbom.json не найден")
        self.log_area.append("✅ SBOM прочитан")

        # 2. Хэши
        results = sbom.check_components_hashes(str(base_dir))
        if any(not v for v in results.values()):
            self.log_area.append("❌ Хэши не совпадают")
        else:
            self.log_area.append("✅ Целостность подтверждена")

        # 3. ЭЦП
        checker = IntegrityChecker()
        try:
            with open(base_dir / "manifest.json", "rb") as f: m = f.read()
            with open(base_dir / "manifest.sig", "rb") as f: s = f.read()
            with open(base_dir / "public_key.pem", "rb") as f: p = f.read()
            if checker.verify_signature(m, s, p):
                self.log_area.append("✅ ЭЦП верна")
            else:
                self.log_area.append("❌ ЭЦП неверна")
        except Exception as e:
            self.log_area.append(f"⚠️ Ошибка: {e}")