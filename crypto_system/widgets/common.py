from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout
from PySide6.QtCore import Qt

from theme import T 

def make_separator() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background: {T.BORDER};")
    return line


def make_mini_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {T.TEXT}; font-size: 13px; font-weight: 600;")
    return lbl


def make_kv_row(icon: str, key: str, value: str) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(8)

    if icon:
        ic = QLabel(icon)
        ic.setFixedWidth(18)
        row.addWidget(ic)

    k = QLabel(key)
    k.setStyleSheet(f"color: {T.TEXT_MUTED}; font-size: 12px;")
    row.addWidget(k)

    row.addStretch()

    v = QLabel(value)
    v.setStyleSheet(f"color: {T.TEXT}; font-size: 12px;")
    row.addWidget(v)

    return row