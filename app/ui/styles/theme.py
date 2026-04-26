def get_stylesheet() -> str:
    return """
/* ─── 전체 앱 ─── */
QMainWindow {
    background-color: #F0F2F5;
    font-family: "맑은 고딕";
    font-size: 10pt;
    color: #2D2D2D;
}

/* ─── 사이드바 컨테이너 ─── */
QWidget#Sidebar {
    background-color: #1B2A3B;
}

/* ─── 콘텐츠 영역 ─── */
QWidget#content_area {
    background-color: #F0F2F5;
}

/* ─── 검색바 컨테이너 ─── */
QWidget#search_bar {
    background-color: #FFFFFF;
    border: 1px solid #DDE1E7;
    border-radius: 6px;
}

/* ─── 검색 입력창 ─── */
QLineEdit#search_input {
    border: none;
    background: transparent;
    font-size: 10pt;
    font-family: "맑은 고딕";
    color: #2D2D2D;
    padding: 8px 0px;
}

/* ─── 콤보박스 ─── */
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #DDE1E7;
    border-radius: 6px;
    padding: 6px 10px;
    color: #2D2D2D;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #DDE1E7;
}
QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #7F8C8D;
}

/* ─── 기본 버튼 ─── */
QPushButton#btn_primary {
    background-color: #2E86AB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 10pt;
    font-family: "맑은 고딕";
    font-weight: bold;
}

QPushButton#btn_primary:hover {
    background-color: #2471A3;
}

QPushButton#btn_primary:pressed {
    background-color: #1A5276;
}

QPushButton#btn_secondary {
    background-color: #FFFFFF;
    color: #2D2D2D;
    border: 1px solid #DDE1E7;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 10pt;
    font-family: "맑은 고딕";
}

QPushButton#btn_secondary:hover {
    background-color: #F0F2F5;
}

QPushButton#btn_danger {
    background-color: #E74C3C;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 10pt;
    font-family: "맑은 고딕";
}

QPushButton#btn_danger:hover {
    background-color: #C0392B;
}

/* ─── 테이블 ─── */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #DDE1E7;
    border-radius: 8px;
    gridline-color: #F0F2F5;
    font-size: 10pt;
    font-family: "맑은 고딕";
    color: #2D2D2D;
}

QTableWidget::item {
    padding: 10px 14px;
    border-bottom: 1px solid #F0F2F5;
}

QTableWidget::item:selected {
    background-color: #D6EAF8;
    color: #2D2D2D;
}

QTableWidget::item:hover {
    background-color: #F0F7FF;
}

QHeaderView::section {
    background-color: #F8F9FA;
    color: #7F8C8D;
    font-size: 9pt;
    font-weight: bold;
    font-family: "맑은 고딕";
    padding: 10px 14px;
    border: none;
    border-bottom: 2px solid #DDE1E7;
    border-right: 1px solid #DDE1E7;
}

/* ─── 스크롤바 ─── */
QScrollBar:vertical {
    background-color: #F0F2F5;
    width: 6px;
    border-radius: 3px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #BDC3C7;
    border-radius: 3px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #95A5A6;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ─── 상태바 ─── */
QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #DDE1E7;
    color: #7F8C8D;
    font-size: 9pt;
    font-family: "맑은 고딕";
    padding: 2px 8px;
}

/* ─── 날짜 입력 ─── */
QDateEdit {
    background-color: #FFFFFF;
    border: 1px solid #DDE1E7;
    border-radius: 6px;
    padding: 6px 10px;
    color: #2D2D2D;
}

QDateEdit::drop-down {
    border: none;
    width: 20px;
}

/* ─── 달력 (인라인 임베드) ─── */
QCalendarWidget {
    background-color: #FFFFFF;
    border: 1px solid #DDE1E7;
    border-radius: 8px;
    font-size: 9pt;
}

QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: #2C3E50;
    min-height: 36px;
}

QCalendarWidget QToolButton {
    color: #FFFFFF;
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: bold;
    font-size: 9pt;
}

QCalendarWidget QToolButton:hover {
    background-color: #2E86AB;
}

QCalendarWidget QToolButton::menu-indicator {
    image: none;
}

QCalendarWidget QMenu {
    background-color: #FFFFFF;
    border: 1px solid #DDE1E7;
    color: #2D2D2D;
}

QCalendarWidget QAbstractItemView {
    background-color: #FFFFFF;
    selection-background-color: #2E86AB;
    selection-color: #FFFFFF;
    color: #2D2D2D;
    alternate-background-color: #F8F9FA;
}

QCalendarWidget QAbstractItemView:disabled {
    color: #BDC3C7;
}
"""
