"""사건 상세 다이얼로그."""
from PySide6.QtCore import QDate, Qt, Signal, QObject, QEvent
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListView,
    QMessageBox,
    QPushButton,
    QStyledItemDelegate,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

REFUND_REASONS = ["대출취소", "중복납부", "착오납부", "기타"]
FONT = QFont("맑은 고딕", 10)

_DETAIL_QSS = """
QDialog#case_detail_dialog {
    background-color: #F0F2F5;
    font-family: '맑은 고딕';
    color: #2D2D2D;
}
QWidget#detail_tab_page {
    background-color: #FFFFFF;
}
QLabel#field_label {
    color: #2D2D2D;
    background: transparent;
    font-size: 10pt;
}
QLabel#field_subtext {
    color: #7F8C8D;
    background: transparent;
    font-size: 9pt;
}
QLabel#status_value {
    color: #2D2D2D;
    font-weight: 600;
    font-size: 10pt;
    background: transparent;
}
QLineEdit, QDateEdit, QTextEdit, QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #DDE1E7;
    border-radius: 6px;
    padding: 6px 10px;
    color: #2D2D2D;
    font-family: '맑은 고딕';
    font-size: 10pt;
}
QLineEdit:focus, QDateEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #2E86AB;
}
QDateEdit::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border-left: 1px solid #E6ECF2;
    background: #FAFBFD;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border-left: 1px solid #E6ECF2;
    background: #FAFBFD;
}
QTabWidget::pane {
    border: 1px solid #DDE1E7;
    border-radius: 8px;
    background: #FFFFFF;
    top: -1px;
}
QTabBar::tab {
    background: #F0F2F5;
    color: #7F8C8D;
    padding: 8px 16px;
    border: none;
    font-size: 10pt;
}
QTabBar::tab:selected {
    background: #FFFFFF;
    color: #2D2D2D;
    font-weight: bold;
    border-bottom: 2px solid #2E86AB;
}
QFrame#status_panel {
    background-color: #FFFFFF;
    border: 1px solid #DDE1E7;
    border-radius: 6px;
}
QPushButton#btn_primary {
    background-color: #2E86AB;
    color: #FFFFFF;
    border: none;
    border-radius: 7px;
    font-weight: 600;
    padding: 8px 14px;
}
QPushButton#btn_primary:hover { background-color: #2471A3; }
QPushButton#btn_secondary {
    background-color: #FFFFFF;
    color: #2D2D2D;
    border: 1px solid #DDE1E7;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: bold;
}
QPushButton#btn_secondary:hover { background-color: #F0F2F5; }
QPushButton#btn_secondary:disabled {
    background-color: #F8F9FA;
    color: #A5AFBA;
    border: 1px solid #DDE1E7;
}
QTableWidget#history_table {
    background-color: #FFFFFF;
    border: none;
    gridline-color: #F0F2F5;
}
QTableWidget#history_table::item {
    padding: 8px;
    color: #2D2D2D;
    border: none;
}
QTableWidget#history_table::item:selected {
    background-color: #EAF3FB;
    color: #2D2D2D;
}
QHeaderView::section {
    background-color: #F8F9FA;
    color: #7F8C8D;
    font-weight: bold;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #DDE1E7;
}
"""


class _ComboArrowEventFilter(QObject):
    """콤보박스 크기 변경 시 ▾ 오버레이 위치를 유지한다."""

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            arrow = getattr(watched, "_arrow_label", None)
            if arrow is not None:
                arrow.move(watched.width() - 18, (watched.height() - 16) // 2)
        return super().eventFilter(watched, event)


_COMBO_ARROW_FILTER = _ComboArrowEventFilter()


def _apply_combo_popup_style(combo: QComboBox) -> None:
    """메인 화면 상태 콤보와 동일한 팝업 라이트 테마 적용."""
    view = combo.view()
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
            border: 1px solid #DDE1E7;
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
        | Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.NoDropShadowWindowHint
    )
    popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    popup.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
    popup.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
    popup.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    popup.setStyleSheet("background-color: #FFFFFF; border: none;")
    view.window().setStyleSheet("background-color: #FFFFFF; border: none;")


def _build_combo() -> QComboBox:
    combo = QComboBox()
    combo.setView(QListView())
    combo.setFixedHeight(36)
    combo.setItemDelegate(QStyledItemDelegate(combo))
    _apply_combo_popup_style(combo)
    _attach_combo_arrow(combo)
    return combo


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


class CaseDetailDialog(QDialog):
    updated = Signal()

    def __init__(self, case_id: int, parent=None):
        super().__init__(parent)
        self.case_id = case_id
        self._status = "CREATED"

        self.setObjectName("case_detail_dialog")
        self.setWindowTitle("사건 상세")
        self.setModal(True)
        self.resize(640, 720)
        self.setFont(FONT)
        self.setStyleSheet(_DETAIL_QSS)

        self._build_ui()
        self._load_clients()
        self._load_case()
        self._load_history()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, stretch=1)

        self._build_tab_basic()
        self._build_tab_history()
        self._build_tab_memo()

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("field_label")
        return label

    def _build_tab_basic(self):
        tab = QWidget()
        tab.setObjectName("detail_tab_page")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.payer_input = QLineEdit()
        self.payer_input.setFixedHeight(36)
        form.addRow(self._field_label("납세자명"), self.payer_input)

        self.paid_date_edit = QDateEdit()
        self.paid_date_edit.setCalendarPopup(True)
        self.paid_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.paid_date_edit.setFixedHeight(36)
        form.addRow(self._field_label("납부일"), self.paid_date_edit)

        self.tax_input = QLineEdit()
        self.tax_input.setFixedHeight(36)
        self.tax_input.textChanged.connect(self._format_tax)
        form.addRow(self._field_label("세액"), self.tax_input)

        self.reason_combo = _build_combo()
        self.reason_combo.addItems(REFUND_REASONS)
        form.addRow(self._field_label("환급사유"), self.reason_combo)

        self.client_combo = _build_combo()
        self.client_combo.addItem("(선택 안함)", None)
        form.addRow(self._field_label("거래처"), self.client_combo)

        self.handler_input = QLineEdit()
        self.handler_input.setFixedHeight(36)
        form.addRow(self._field_label("담당자"), self.handler_input)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save_basic = QPushButton("저장")
        btn_save_basic.setObjectName("btn_primary")
        btn_save_basic.setFixedHeight(36)
        btn_save_basic.clicked.connect(self._on_save_basic)
        btn_row.addWidget(btn_save_basic)
        layout.addLayout(btn_row)

        status_panel = QFrame()
        status_panel.setObjectName("status_panel")
        status_layout = QHBoxLayout(status_panel)
        status_layout.setContentsMargins(14, 12, 14, 12)
        status_layout.setSpacing(12)

        status_text_layout = QVBoxLayout()
        status_text_layout.setContentsMargins(0, 0, 0, 0)
        status_text_layout.setSpacing(3)

        status_caption = QLabel("현재 상태")
        status_caption.setObjectName("field_subtext")
        self.status_label = QLabel("-")
        self.status_label.setObjectName("status_value")
        status_text_layout.addWidget(status_caption)
        status_text_layout.addWidget(self.status_label)

        status_layout.addLayout(status_text_layout)
        status_layout.addStretch()

        self.btn_next_status = QPushButton("다음 단계로")
        self.btn_next_status.setObjectName("btn_secondary")
        self.btn_next_status.setFixedHeight(36)
        self.btn_next_status.clicked.connect(self._on_advance_status)
        status_layout.addWidget(self.btn_next_status)
        layout.addWidget(status_panel)
        layout.addStretch()

        self.tabs.addTab(tab, "기본정보")

    def _build_tab_history(self):
        tab = QWidget()
        tab.setObjectName("detail_tab_page")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        helper = QLabel("상태 변경 이력이 자동 기록됩니다.")
        helper.setObjectName("field_subtext")
        layout.addWidget(helper)

        self.history_table = QTableWidget()
        self.history_table.setObjectName("history_table")
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["처리일시", "내용", "처리자"])
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.history_table.setShowGrid(False)
        self.history_table.setWordWrap(False)
        self.history_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.verticalHeader().setDefaultSectionSize(40)

        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.history_table.setColumnWidth(0, 140)
        self.history_table.setColumnWidth(2, 150)

        layout.addWidget(self.history_table, stretch=1)
        self.tabs.addTab(tab, "진행이력")

    def _build_tab_memo(self):
        tab = QWidget()
        tab.setObjectName("detail_tab_page")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        helper = QLabel("사건 관련 메모를 저장하면 다음 열람 시에도 유지됩니다.")
        helper.setObjectName("field_subtext")
        layout.addWidget(helper)

        self.memo_edit = QTextEdit()
        self.memo_edit.setPlaceholderText("메모를 입력하세요.")
        layout.addWidget(self.memo_edit, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save = QPushButton("저장")
        btn_save.setObjectName("btn_primary")
        btn_save.setFixedHeight(36)
        btn_save.clicked.connect(self._on_save_memo)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        self.tabs.addTab(tab, "메모")

    def _set_status_ui(self, status_code: str, status_label: str):
        self._status = status_code
        self.status_label.setText(status_label)
        self.btn_next_status.setEnabled(status_code != "CLOSED")

    def _load_clients(self):
        try:
            from app.services.client_service import list_clients

            for client in list_clients():
                self.client_combo.addItem(client.client_name, client.id)
        except Exception:
            pass

    def _load_case(self):
        from app.services.case_service import STATUS_LABELS, get_case

        case = get_case(self.case_id)
        if not case:
            QMessageBox.warning(self, "조회 실패", "사건 정보를 찾을 수 없습니다.")
            self.reject()
            return

        self.payer_input.setText(case.get("payer_name", "") or "")

        paid_date = QDate.fromString(case.get("paid_date", "") or "", "yyyy-MM-dd")
        self.paid_date_edit.setDate(paid_date if paid_date.isValid() else QDate.currentDate())

        tax_total = case.get("tax_total", 0) or 0
        self.tax_input.setText(f"{int(tax_total):,}" if str(tax_total).strip() else "")

        reason = case.get("refund_reason", "") or ""
        reason_idx = self.reason_combo.findText(reason)
        if reason_idx < 0 and reason:
            self.reason_combo.addItem(reason)
            reason_idx = self.reason_combo.findText(reason)
        if reason_idx >= 0:
            self.reason_combo.setCurrentIndex(reason_idx)

        client_id = case.get("client_id")
        client_idx = self.client_combo.findData(client_id)
        if client_idx >= 0:
            self.client_combo.setCurrentIndex(client_idx)
        else:
            self.client_combo.setCurrentIndex(0)

        self.handler_input.setText(case.get("handler", "") or "")
        self.memo_edit.setPlainText(case.get("memo", "") or "")

        current_status = case.get("status", "CREATED") or "CREATED"
        self._set_status_ui(current_status, STATUS_LABELS.get(current_status, current_status))

    def _load_history(self):
        from app.services.case_service import list_case_events

        events = list_case_events(self.case_id)
        self.history_table.setRowCount(0)

        for event in events:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            self.history_table.setRowHeight(row, 40)

            processed_at = str(event.get("processed_at", "") or "")
            if len(processed_at) >= 16:
                processed_at = processed_at[:16]

            content = str(event.get("content", "") or "")
            actor = str(event.get("actor", "") or "")

            col0 = QTableWidgetItem(processed_at)
            col0.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            col1 = QTableWidgetItem(content)
            col1.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            col1.setToolTip(content)

            col2 = QTableWidgetItem(actor)
            col2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            col2.setToolTip(actor)

            self.history_table.setItem(row, 0, col0)
            self.history_table.setItem(row, 1, col1)
            self.history_table.setItem(row, 2, col2)

    def _format_tax(self, text: str):
        digits = "".join(ch for ch in text if ch.isdigit())
        formatted = f"{int(digits):,}" if digits else ""
        if self.tax_input.text() != formatted:
            self.tax_input.blockSignals(True)
            self.tax_input.setText(formatted)
            self.tax_input.blockSignals(False)

    def _tax_int(self) -> int:
        digits = "".join(ch for ch in self.tax_input.text() if ch.isdigit())
        return int(digits) if digits else 0

    def _on_save_basic(self):
        payer_name = self.payer_input.text().strip()
        paid_date = self.paid_date_edit.date().toString("yyyy-MM-dd")
        tax_total = self._tax_int()

        if not payer_name:
            QMessageBox.warning(self, "입력 오류", "납세자명을 입력하세요.")
            self.payer_input.setFocus()
            return
        if tax_total <= 0:
            QMessageBox.warning(self, "입력 오류", "세액을 올바르게 입력하세요.")
            self.tax_input.setFocus()
            return

        try:
            from app.services.case_service import update_case_basic

            update_case_basic(
                case_id=self.case_id,
                payer_name=payer_name,
                paid_date=paid_date,
                tax_total=tax_total,
                refund_reason=self.reason_combo.currentText(),
                client_id=self.client_combo.currentData(),
                handler=self.handler_input.text().strip() or None,
            )
            self.updated.emit()
            QMessageBox.information(self, "저장 완료", "기본정보를 저장했습니다.")
        except Exception as exc:
            QMessageBox.critical(self, "저장 실패", str(exc))

    def _on_save_memo(self):
        try:
            from app.services.case_service import update_case_memo

            update_case_memo(self.case_id, self.memo_edit.toPlainText().strip())
            self.updated.emit()
            QMessageBox.information(self, "저장 완료", "메모를 저장했습니다.")
        except Exception as exc:
            QMessageBox.critical(self, "저장 실패", str(exc))

    def _on_advance_status(self):
        if self._status == "CLOSED":
            self.btn_next_status.setEnabled(False)
            return

        default_date = QDate.currentDate().toString("yyyy-MM-dd")
        event_date, ok = QInputDialog.getText(
            self,
            "처리일 입력",
            "처리일(YYYY-MM-DD):",
            text=default_date,
        )
        if not ok:
            return

        event_date = event_date.strip()
        parsed = QDate.fromString(event_date, "yyyy-MM-dd")
        if not parsed.isValid():
            QMessageBox.warning(self, "입력 오류", "날짜 형식은 YYYY-MM-DD 이어야 합니다.")
            return

        try:
            from app.services.case_service import STATUS_LABELS, advance_case_status

            next_status = advance_case_status(
                case_id=self.case_id,
                event_date=event_date,
                actor=self.handler_input.text().strip() or None,
            )
            if next_status is None:
                self._set_status_ui("CLOSED", STATUS_LABELS["CLOSED"])
                QMessageBox.information(self, "안내", "이미 종결 상태입니다.")
                return

            self._set_status_ui(next_status, STATUS_LABELS.get(next_status, next_status))
            self._load_history()
            self.updated.emit()
        except Exception as exc:
            QMessageBox.critical(self, "상태 변경 실패", str(exc))
