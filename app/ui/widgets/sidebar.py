from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon, QPalette, QColor


class SidebarWidget(QWidget):
    menu_clicked = Signal(str)

    # (key, 표시 텍스트, 이모지 아이콘)
    MENU_ITEMS = [
        ("refund",  "환급관리",  "▣"),
        ("cases",   "사건 관리", "▤"),
        ("clients", "거래처 관리", "▥"),
        ("office",  "사무소 정보", "◌"),
    ]
    MENU_STYLE_INACTIVE = (
        "QPushButton {"
        " color: #D8E2EC;"
        " background: transparent;"
        " text-align: left;"
        " padding: 10px 16px;"
        " border-radius: 8px;"
        " border: none;"
        " font-size: 10pt;"
        "}"
        "QPushButton:hover {"
        " background-color: #243447;"
        " color: #FFFFFF;"
        "}"
    )
    MENU_STYLE_ACTIVE = (
        "QPushButton {"
        " color: #FFFFFF;"
        " background-color: #2E86AB;"
        " text-align: left;"
        " padding: 10px 16px;"
        " border-radius: 8px;"
        " border: none;"
        " font-size: 10pt;"
        " font-weight: bold;"
        "}"
        "QPushButton:hover {"
        " background-color: #2E86AB;"
        " color: #FFFFFF;"
        "}"
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(260)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1B2A3B"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        # QSS는 보조로만 유지 (Fusion 스타일 오버라이드 대비).
        self.setStyleSheet(
            "#Sidebar { background-color: #1B2A3B; }"
            "#Sidebar QWidget { background-color: transparent; }"
        )
        self._buttons: dict[str, QPushButton] = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(0)

        header = QWidget()
        header.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        header.setAutoFillBackground(False)
        header.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 2, 8, 2)
        header_layout.setSpacing(8)

        icon_label = QLabel()
        app_icon = QIcon("assets/icons/app_icon.ico")
        pixmap = app_icon.pixmap(16, 16)
        if pixmap.isNull():
            icon_label.setText("▣")
            icon_label.setStyleSheet(
                "color: #D8E2EC; font-size: 10pt; background: transparent;"
            )
        else:
            icon_label.setPixmap(pixmap)
            icon_label.setStyleSheet("background: transparent;")

        title_text = QLabel("등록면허세 환급관리")
        title_text.setStyleSheet(
            "color: #E8EEF5;"
            " font-size: 10.5pt;"
            " font-weight: bold;"
            " background: transparent;"
        )
        subtitle_text = QLabel("업무 관리 시스템")
        subtitle_text.setStyleSheet(
            "color: #91A2B5;"
            " font-size: 8pt;"
            " background: transparent;"
        )

        text_stack = QVBoxLayout()
        text_stack.setContentsMargins(0, 0, 0, 0)
        text_stack.setSpacing(0)
        text_stack.addWidget(title_text)
        text_stack.addWidget(subtitle_text)

        header_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignTop)
        header_layout.addLayout(text_stack)
        header_layout.addStretch()

        layout.addWidget(header)
        layout.addSpacing(18)

        btn_container = QWidget()
        btn_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        btn_container.setAutoFillBackground(False)
        btn_container.setStyleSheet("background: transparent;")
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(4)

        for key, label, icon in self.MENU_ITEMS:
            btn = QPushButton(f"{icon}  {label}")
            btn.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            btn.setAutoFillBackground(False)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(44)
            btn.setStyleSheet(self.MENU_STYLE_INACTIVE)
            btn.clicked.connect(lambda _, k=key: self._on_click(k))
            self._buttons[key] = btn
            btn_layout.addWidget(btn)

        layout.addWidget(btn_container)
        layout.addStretch()

        from app.ui.widgets.summary_widget import SummaryWidget
        self.summary = SummaryWidget()
        self.summary.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.summary.setAutoFillBackground(False)
        layout.addWidget(self.summary)

    def _on_click(self, key: str):
        for k, btn in self._buttons.items():
            btn.setStyleSheet(
                self.MENU_STYLE_ACTIVE if k == key else self.MENU_STYLE_INACTIVE
            )
        self.menu_clicked.emit(key)

    def set_active(self, key: str):
        self._on_click(key)
