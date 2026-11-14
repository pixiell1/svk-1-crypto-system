from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QTextEdit, QComboBox
)
from PySide6.QtCore import Qt
from theme import T
from core.rng import (
    Rng, RngDescriptor, EntropySource, SourceType,
    MixMethod, RngConfig, read_urandom
)
from core.audit import EventCategory, EventStatus, EventLevel
from core.storage import KeyStorage  # <-- Импортируем хранилище

class KeyGenPage(QWidget):
    def __init__(self, audit, on_generate=None):
        super().__init__()
        self._audit = audit
        self._on_generate = on_generate
        self._rng = None 
        self._storage = KeyStorage()

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(20)

        title = QLabel("🔑  Генерация ключей")
        title.setStyleSheet("font-size: 26px; font-weight: 700; color: #ffffff;")
        v.addWidget(title)

        card = QFrame()
        card.setObjectName("Card")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(24, 24, 24, 24)
        cv.setSpacing(14)

        cv.addWidget(QLabel("Алгоритм:"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems([
            "ECDSA (P-256)", "ECDSA (P-384)", "RSA-2048", "RSA-4096",
            "СТБ 34.101.47 (п. 6.2)", "СТБ 34.101.47 (п. 6.3)"
        ])
        cv.addWidget(self.algo_combo)

        cv.addWidget(QLabel("Длина ключа:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(["512 бит", "1024 бит", "2048 бит", "3072 бита", "4096 бит"])
        self.size_combo.setCurrentText("2048 бит")
        cv.addWidget(self.size_combo)

        row = QHBoxLayout()
        row.addStretch()
        self.gen_btn = QPushButton("Сгенерировать ключевую пару")
        self.gen_btn.setObjectName("Primary")
        self.gen_btn.setCursor(Qt.PointingHandCursor)
        self.gen_btn.clicked.connect(self._do_generate)
        row.addWidget(self.gen_btn)
        cv.addLayout(row)

        cv.addWidget(QLabel("Результат:"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(200)
        self.log.setStyleSheet(f"""
            QTextEdit {{
                background: {T.BG};
                border: 1px solid {T.BORDER};
                border-radius: 6px;
                color: {T.TEXT};
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 8px;
            }}
        """)
        cv.addWidget(self.log)

        v.addWidget(card)
        v.addStretch()

    def append_log(self, text: str):
        self.log.append(text)

    def _do_generate(self):
        self.log.clear()
        self.append_log("Инициализация ГСЧ...")
        self.gen_btn.setEnabled(False)
        
        success = False
        err_msg = ""
        key_hex = ""
        length_text = self.size_combo.currentText()
        algo_text = self.algo_combo.currentText()

        try:
            descriptor = RngDescriptor(
                name="main-rng",
                mix_method=MixMethod.HASH,
                mix_algorithm="sha256",
                purpose="выработка ключей",
                sources=[
                    EntropySource("urandom", SourceType.SYSTEM, read_urandom, 8.0, is_ksk=False),
                ],
            )

            self._rng = Rng(descriptor)
            self._rng.validate()
            self._rng.init(
                config=RngConfig(check_sources_before_keygen=False, strict_mode=False),
                log_callback=self.append_log 
            )

            length_bytes = int(length_text.split()[0]) // 8
            self.append_log(f"\nГенерация ключа ({length_text})...")
            
            key_bytes = self._rng.generate_key(length_bytes)
            key_hex = key_bytes.hex()

            self.append_log(f"УСПЕХ! Личный ключ (hex):\n{key_hex}")
            success = True

            # 6. СОХРАНЯЕМ В ХРАНИЛИЩЕ
            self._storage.add_key(key_hex, int(length_text.split()[0]), algo_text)
            self.append_log("✅ Ключ сохранен в хранилище.")

            self._rng.wipe_state()

        except Exception as e:
            err_msg = str(e)
            self.append_log(f"\nОШИБКА: {err_msg}")

        finally:
            if self._audit:
                if success:
                    self._audit.log(
                        source="keygen", user="admin",
                        description=f"Генерация ключа ({algo_text}, {length_text})",
                        category=EventCategory.OBJECT,
                        status=EventStatus.SUCCESS,
                    )
                else:
                    self._audit.log(
                        source="keygen", user="admin",
                        description=f"Ошибка генерации: {err_msg}",
                        category=EventCategory.OBJECT,
                        status=EventStatus.FAILURE,
                        level=EventLevel.CRITICAL
                    )

            self.gen_btn.setEnabled(True)
            if success and self._on_generate:
                self._on_generate()