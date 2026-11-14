from PySide6.QtWidgets import QApplication


class T:
    BG          = "#0a1424"
    BG_SIDEBAR  = "#0d1b30"
    BG_TOPBAR   = "#0d1b30"
    BG_CARD     = "#101f38"
    BG_CARD_HOV = "#152947"
    BG_HERO     = "#0f2544"
    BORDER      = "#1b3252"
    TEXT        = "#e8eef7"
    TEXT_MUTED  = "#7c8fa8"
    ACCENT      = "#22d3ee"
    ACCENT_DIM  = "#0e7490"
    GREEN       = "#22c55e"
    RED         = "#ef4444"
    YELLOW      = "#f59e0b"
    ORANGE      = "#f97316"
    BLUE        = "#3b82f6"


def apply_theme(app: QApplication):
    app.setStyleSheet(f"""
    * {{
        font-family: "Segoe UI", "Inter", sans-serif;
        color: {T.TEXT};
    }}
    QMainWindow, QWidget {{
        background: {T.BG};
    }}
    QFrame#Sidebar {{
        background: {T.BG_SIDEBAR};
        border-right: 1px solid {T.BORDER};
    }}
    QFrame#TopBar {{
        background: {T.BG_TOPBAR};
        border-bottom: 1px solid {T.BORDER};
    }}
    QLabel#AppTitle {{
        font-size: 18px;
        font-weight: 700;
        color: {T.TEXT};
    }}
    QLabel#AppSubtitle {{
        font-size: 12px;
        color: {T.TEXT_MUTED};
    }}
    QLabel#HeroTitle {{
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
    }}
    QLabel#HeroSubtitle {{
        font-size: 14px;
        color: {T.ACCENT};
    }}
    QLabel#HeroMeta {{
        font-size: 13px;
        color: {T.TEXT_MUTED};
    }}
    QLabel#SectionTitle {{
        font-size: 15px;
        font-weight: 600;
        color: {T.TEXT};
    }}
    QLabel#CardTitle {{
        font-size: 15px;
        font-weight: 600;
        color: #ffffff;
    }}
    QLabel#CardText {{
        font-size: 12px;
        color: {T.TEXT_MUTED};
    }}
    QPushButton#NavButton {{
        background: transparent;
        border: none;
        border-left: 3px solid transparent;
        text-align: left;
        padding: 12px 18px;
        font-size: 14px;
        color: {T.TEXT_MUTED};
    }}
    QPushButton#NavButton:hover {{
        background: {T.BG_CARD};
        color: {T.TEXT};
    }}
    QPushButton#NavButton:checked {{
        background: {T.BG_CARD};
        color: {T.ACCENT};
        border-left: 3px solid {T.ACCENT};
        font-weight: 600;
    }}
    QFrame#Card {{
        background: {T.BG_CARD};
        border: 1px solid {T.BORDER};
        border-radius: 10px;
    }}
    QFrame#Hero {{
        background: {T.BG_HERO};
        border: 1px solid {T.BORDER};
        border-radius: 12px;
    }}
    QTableWidget {{
        background: {T.BG_CARD};
        border: none;
        gridline-color: {T.BORDER};
        font-size: 13px;
    }}
    QTableWidget::item {{
        padding: 8px;
        border-bottom: 1px solid {T.BORDER};
    }}
    QHeaderView::section {{
        background: {T.BG_CARD};
        color: {T.TEXT_MUTED};
        border: none;
        padding: 10px 8px;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton#Primary {{
        background: {T.ACCENT};
        color: #04121f;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 600;
    }}
    QPushButton#Primary:hover {{
        background: #67e8f9;
    }}
    QPushButton#Ghost {{
        background: transparent;
        color: {T.ACCENT};
        border: 1px solid {T.ACCENT_DIM};
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 12px;
    }}
    QPushButton#Ghost:hover {{
        background: {T.BG_CARD_HOV};
    }}
    QLabel#StatusOk {{
        color: {T.GREEN};
        font-size: 22px;
        font-weight: 700;
    }}
    QLabel#StatusSub {{
        color: {T.TEXT_MUTED};
        font-size: 12px;
    }}
    QFrame#StatusDot {{
        background: {T.GREEN};
        border-radius: 6px;
    }}
    """)