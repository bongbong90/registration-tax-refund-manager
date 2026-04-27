from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QComboBox, QPushButton, QLabel,
    QStackedWidget, QFrame, QListView,
    QStyledItemDelegate, QStyle, QMenu,
)
from PySide6.QtCore import Signal, Qt, QTimer, QRect, QObject, QEvent
from PySide6.QtGui import QColor, QPixmap, QPainter, QPen, QPalette, QFont


STATUS_LABELS = {
    "CREATED":       "서류생성",
    "SENT_TO_BANK":  "은행송부",
    "BANK_RETURNED": "은행회신",
    "SUBMITTED":     "구청접수",
    "REFUND_DECIDED": "환급결정",
    "DEPOSITED":     "입금확인",
    "CLOSED":        "종결",
}

ROW_BG = ("#FFFFFF", "#F8F9FA")  # 짝수, 홀수


class _ComboArrowEventFilter(QObject):
    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            arrow = getattr(watched, "_arrow_label", None)
            if arrow is not None:
                arrow.move(watched.width() - 18, (watched.height() - 16) // 2)
        return super().eventFilter(watched, event)


_COMBO_ARROW_FILTER = _ComboArrowEventFilter()


class StatusDelegate(QStyledItemDelegate):
    STATUS_STYLE = {
        "서류생성": ("#E8F4FD", "#2E86AB"),
        "은행송부": ("#FEF9E7", "#F39C12"),
        "은행회신": ("#FEF9E7", "#F39C12"),
        "구청접수": ("#FEF9E7", "#F39C12"),
        "환급결정": ("#E8F8F5", "#27AE60"),
        "입금확인": ("#E8F8F5", "#27AE60"),
        "종결":     ("#F2F3F4", "#7F8C8D"),
    }

    def paint(self, painter, option, index):
        text = index.data(Qt.ItemDataRole.DisplayRole)
        bg, fg = self.STATUS_STYLE.get(text, ("#F2F3F4", "#7F8C8D"))

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        base_brush = index.data(Qt.ItemDataRole.BackgroundRole)
        base_color = QColor("#FFFFFF")
        if hasattr(base_brush, "color"):
            base_color = base_brush.color()

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#D6EAF8"))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor("#EBF5FB"))
        else:
            painter.fillRect(option.rect, base_color)

        badge_w = 80
        badge_h = 24
        x = option.rect.x() + (option.rect.width() - badge_w) // 2
        y = option.rect.y() + (option.rect.height() - badge_h) // 2
        badge_rect = QRect(x, y, badge_w, badge_h)

        painter.setBrush(QColor(bg))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(badge_rect, 12, 12)

        font = QFont("맑은 고딕", 9)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(fg))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()


class AlignedPopupComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._avoid_widget: QWidget | None = None
        self._avoid_gap = 14

    def set_avoid_widget(self, widget: QWidget, gap: int = 14):
        self._avoid_widget = widget
        self._avoid_gap = gap

    def showPopup(self):
        super().showPopup()
        QTimer.singleShot(0, self._align_popup_geometry)

    def _align_popup_geometry(self):
        view = self.view()
        popup = view.window()
        popup_pos = self.mapToGlobal(self.rect().bottomLeft())
        popup_width = self.width()

        if self._avoid_widget is not None and self._avoid_widget.isVisible():
            avoid_left = self._avoid_widget.mapToGlobal(
                self._avoid_widget.rect().topLeft()
            ).x()
            max_allowed = avoid_left - self._avoid_gap - popup_pos.x()
            popup_width = min(popup_width + 10, max(140, max_allowed))

        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            popup_width = min(
                popup_width, max(140, available.right() - popup_pos.x() - 4)
            )

        row_height = max(view.sizeHintForRow(0), 32)
        visible_rows = min(max(1, self.count()), 10)
        popup_height = visible_rows * row_height + 6

        popup.setGeometry(
            popup_pos.x(),
            popup_pos.y() + 1,
            popup_width,
            popup_height,
        )
        popup.setContentsMargins(0, 0, 0, 0)
        view.setContentsMargins(0, 0, 0, 0)
        view.setViewportMargins(0, 0, 0, 0)
        view.move(0, 0)
        view.setFixedWidth(popup_width)
        view.setFixedHeight(popup_height)


def _attach_combo_arrow(combo: QComboBox) -> None:
    arrow = QLabel("▾", combo)
    arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    arrow.setStyleSheet(
        "color: #7F8C8D; font-size: 11pt; font-weight: bold; background: transparent;"
    )
    arrow.setFixedSize(12, 16)
    arrow.show()
    combo._arrow_label = arrow
    combo.installEventFilter(_COMBO_ARROW_FILTER)
    arrow.move(combo.width() - 18, (combo.height() - 16) // 2)


class CaseTableWidget(QWidget):
    case_selected = Signal(int)
    add_requested = Signal()
    copy_requested = Signal(int)

    COLUMNS    = ["납부일", "납세자", "세액", "환급사유", "상태"]
    COL_WIDTHS = [112, 0, 116, 150, 116]  # 0 = stretch

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("content_area")
        self._cases: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(14)
        top_bar.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        search_bar = QWidget()
        search_bar.setObjectName("search_bar")
        search_bar.setFixedHeight(42)
        sb_layout = QHBoxLayout(search_bar)
        sb_layout.setContentsMargins(12, 0, 12, 0)
        sb_layout.setSpacing(6)

        search_icon = QLabel("⌕")
        search_icon.setStyleSheet(
            "color: #7F8C8D; font-size: 11pt; background: transparent;"
        )
        search_icon.setFixedWidth(18)
        sb_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("search_input")
        self.search_input.setPlaceholderText("납세자명 검색...")
        self.search_input.textChanged.connect(self._apply_filter)
        sb_layout.addWidget(self.search_input)

        top_bar.addWidget(search_bar, stretch=1)

        btn_search = QPushButton("검색")
        btn_search.setFixedSize(64, 42)
        btn_search.setCursor(Qt.PointingHandCursor)
        btn_search.setStyleSheet(
            "QPushButton {"
            " background-color: #F0F2F5;"
            " border: 1px solid #DDE1E7;"
            " border-radius: 6px;"
            " color: #2D2D2D;"
            " font-size: 10pt;"
            " font-family: '맑은 고딕';"
            "}"
            "QPushButton:hover { background-color: #DDE1E7; }"
        )
        btn_search.clicked.connect(self._apply_filter)
        self.search_input.returnPressed.connect(self._apply_filter)
        top_bar.addWidget(btn_search)

        self.status_filter = AlignedPopupComboBox()
        self.status_filter.setFixedSize(160, 42)
        self.status_filter.setView(QListView())
        self.status_filter.setItemDelegate(QStyledItemDelegate(self.status_filter))
        self.status_filter.setStyleSheet(
            """
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #DDE1E7;
                border-radius: 8px;
                padding: 8px 12px;
                color: #2D2D2D;
                min-width: 150px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 26px;
                border-left: 1px solid #E6ECF2;
                background: #FAFBFD;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                border: none;
                outline: none;
                padding: 4px 0px;
            }
            QComboBox QAbstractItemView::item {
                background-color: #FFFFFF;
                color: #2D2D2D;
                min-height: 32px;
                padding: 6px 12px;
                border: none;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #F3F7FB;
                color: #2D2D2D;
                border: none;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #EAF3FB;
                color: #2D2D2D;
                border: none;
            }
            """
        )
        _attach_combo_arrow(self.status_filter)
        self.status_filter.addItem("전체 상태", "ALL")
        for key, label in STATUS_LABELS.items():
            self.status_filter.addItem(label, key)
        self.status_filter.currentIndexChanged.connect(self._apply_filter)
        top_bar.addWidget(self.status_filter, alignment=Qt.AlignmentFlag.AlignVCenter)

        btn_add = QPushButton("+ 새 사건")
        btn_add.setObjectName("btn_primary")
        btn_add.setFixedSize(112, 42)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet(
            "QPushButton {"
            " background-color: #2E86AB;"
            " color: #FFFFFF;"
            " border: none;"
            " border-radius: 8px;"
            " font-weight: bold;"
            " padding: 8px 16px;"
            " font-size: 10pt;"
            " font-family: '맑은 고딕';"
            "}"
            "QPushButton:hover {"
            " background-color: #247393;"
            "}"
        )
        btn_add.clicked.connect(self.add_requested.emit)
        top_bar.addWidget(btn_add, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.status_filter.set_avoid_widget(btn_add, gap=14)
        self._configure_status_filter_popup()

        layout.addLayout(top_bar)

        content_card = QFrame()
        content_card.setObjectName("content_card")
        content_card.setStyleSheet(
            "#content_card {"
            " background-color: #FFFFFF;"
            " border: 1px solid #DDE1E7;"
            " border-radius: 12px;"
            "}"
            "#content_card QWidget { background: transparent; }"
        )
        card_layout = QVBoxLayout(content_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self.table_stack = QStackedWidget()
        card_layout.addWidget(self.table_stack, stretch=1)

        empty_widget = QWidget()
        empty_widget.setStyleSheet("background: transparent;")
        ev_layout = QVBoxLayout(empty_widget)
        ev_layout.setAlignment(Qt.AlignCenter)
        ev_layout.setSpacing(10)

        empty_icon = QLabel()
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_icon.setPixmap(self._build_empty_icon_pixmap())

        empty_text = QLabel("표시할 데이터가 없습니다.")
        empty_text.setAlignment(Qt.AlignCenter)
        empty_text.setStyleSheet(
            "font-size: 11pt; color: #A5AFBA;"
            " font-family: '맑은 고딕'; background: transparent;"
        )

        ev_layout.addWidget(empty_icon)
        ev_layout.addWidget(empty_text)
        self.table_stack.addWidget(empty_widget)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet(
            "QTableWidget {"
            " background-color: #FFFFFF;"
            " border: none;"
            " border-radius: 0px;"
            "}"
            "QTableWidget::item {"
            " border-bottom: 1px solid #EEF2F6;"
            "}"
            "QHeaderView::section {"
            " background-color: #F8F9FA;"
            " color: #7F8C8D;"
            " font-weight: bold;"
            " font-size: 9pt;"
            " font-family: '맑은 고딕';"
            " padding: 8px;"
            " border: none;"
            " border-right: 1px solid #DDE1E7;"
            " border-bottom: 2px solid #DDE1E7;"
            "}"
            "QHeaderView::section:last {"
            " border-right: none;"
            "}"
        )

        header = self.table.horizontalHeader()
        for i, width in enumerate(self.COL_WIDTHS):
            if width == 0:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.Fixed)
                self.table.setColumnWidth(i, width)

        self.table.setMouseTracking(True)
        self.table.setItemDelegateForColumn(4, StatusDelegate(self))
        self.table.doubleClicked.connect(self._on_double_click)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.table_stack.addWidget(self.table)

        self.table_stack.setCurrentIndex(0)

        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(14, 10, 14, 10)
        footer_layout.setSpacing(0)

        self.count_label = QLabel("전체 0건")
        self.count_label.setStyleSheet(
            "color: #7F8C8D; font-size: 9pt; font-family: '맑은 고딕';"
        )
        footer_layout.addWidget(self.count_label)
        footer_layout.addStretch()
        card_layout.addWidget(footer)

        layout.addWidget(content_card, stretch=1)

    def refresh_from_db(self):
        """DB에서 사건 목록 재조회 후 테이블 갱신."""
        from app.services.case_service import list_cases
        self.load_cases(list_cases())

    def load_cases(self, cases: list[dict]):
        self._cases = cases
        self._apply_filter()

    def _apply_filter(self):
        search = self.search_input.text().strip().lower()
        status_filter = self.status_filter.currentData()

        filtered = [
            c for c in self._cases
            if (not search or search in c.get("payer_name", "").lower())
            and (status_filter == "ALL" or c.get("status") == status_filter)
        ]
        self._render(filtered)

    # 컬럼별 정렬 플래그 (납부일:center, 납세자:left, 세액:right, 환급사유:center)
    _COL_ALIGN = [
        Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
    ]

    def _render(self, cases: list[dict]):
        self.table.setRowCount(0)

        for idx, case in enumerate(cases):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 44)

            row_bg = QColor(ROW_BG[idx % 2])

            # tax_total 콤마 포맷
            tax_raw = case.get("tax_total", "")
            try:
                tax_str = f"{int(tax_raw):,}" if tax_raw != "" else ""
            except (ValueError, TypeError):
                tax_str = str(tax_raw)

            refund_reason = case.get("refund_reason", "")
            texts = [
                case.get("paid_date", ""),
                case.get("payer_name", ""),
                tax_str,
                refund_reason,
            ]
            for col, text in enumerate(texts):
                item = QTableWidgetItem(text)
                item.setTextAlignment(self._COL_ALIGN[col])
                item.setBackground(row_bg)
                if col == 0:
                    item.setData(Qt.UserRole, case.get("id"))
                if col == 3:
                    item.setToolTip(refund_reason)
                self.table.setItem(row, col, item)

            # 상태 — delegate가 뱃지 페인팅
            status = case.get("status", "CREATED")
            status_kor = STATUS_LABELS.get(status, status)
            item = QTableWidgetItem(status_kor)
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            item.setBackground(row_bg)
            self.table.setItem(row, 4, item)

        self.table_stack.setCurrentIndex(1 if cases else 0)
        self.count_label.setText(f"전체 {len(cases)}건")


    def _on_double_click(self, index):
        item = self.table.item(index.row(), 0)
        if item:
            case_id = item.data(Qt.UserRole)
            if case_id is not None:
                self.case_selected.emit(case_id)

    def _open_context_menu(self, pos):
        index = self.table.indexAt(pos)
        if not index.isValid():
            return

        row = index.row()
        self.table.selectRow(row)
        row_item = self.table.item(row, 0)
        if row_item is None:
            return

        case_id = row_item.data(Qt.UserRole)
        if case_id is None:
            return

        menu = QMenu(self)
        copy_action = menu.addAction("사건 복사")
        selected = menu.exec(self.table.viewport().mapToGlobal(pos))
        if selected == copy_action:
            self.copy_requested.emit(int(case_id))

    def _configure_status_filter_popup(self):
        view = self.status_filter.view()
        view.setAlternatingRowColors(False)
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setLineWidth(0)
        view.setSpacing(0)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        popup = view.window()

        popup_palette = popup.palette()
        popup_palette.setColor(QPalette.ColorRole.Window, QColor("#FFFFFF"))
        popup_palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))

        popup.setPalette(popup_palette)
        popup.setAutoFillBackground(True)
        view.setPalette(popup_palette)
        view.setAutoFillBackground(True)
        view.viewport().setPalette(popup_palette)
        view.viewport().setAutoFillBackground(True)

        view.setStyleSheet(
            """
            QListView {
                background-color: #FFFFFF;
                color: #111827;
                border: none;
                outline: 0px;
                padding: 4px 0px;
                show-decoration-selected: 0;
            }
            QListView::item {
                background-color: #FFFFFF;
                color: #111827;
                min-height: 32px;
                padding: 6px 12px;
                border: none;
            }
            QListView::item:hover {
                background-color: #F3F7FB;
                color: #111827;
                border: none;
            }
            QListView::item:selected {
                background-color: #EAF3FB;
                color: #111827;
                border: none;
            }
            """
        )
        view.viewport().setStyleSheet("background-color: #FFFFFF; border: none;")

        popup.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.NoDropShadowWindowHint
        )
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        popup.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        popup.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        popup.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        popup.setStyleSheet("background-color: #FFFFFF; border: none;")

    @staticmethod
    def _build_empty_icon_pixmap() -> QPixmap:
        pixmap = QPixmap(86, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#C8D0DA"))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawRoundedRect(14, 20, 58, 34, 8, 8)
        painter.drawLine(14, 32, 32, 32)
        painter.drawLine(54, 32, 72, 32)
        painter.drawLine(32, 32, 38, 40)
        painter.drawLine(38, 40, 48, 40)
        painter.drawLine(48, 40, 54, 32)

        painter.end()
        return pixmap
