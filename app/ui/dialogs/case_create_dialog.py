"""새 사건 등록 다이얼로그."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QCalendarWidget, QComboBox, QTextEdit,
    QPushButton, QLabel, QMessageBox, QFrame, QWidget, QListView,
    QStyledItemDelegate, QSizePolicy,
)
from PySide6.QtCore import Qt, QDate, QTimer, QObject, QEvent
from PySide6.QtGui import QFont


REFUND_REASONS = ["대출취소", "중복납부", "착오납부", "기타"]

_FONT = QFont("맑은 고딕", 10)

_FIELD_QSS = (
    "QLineEdit, QTextEdit {"
    " border: 1px solid #DDE1E7; border-radius: 6px;"
    " padding: 6px 10px; font-size: 10pt;"
    " font-family: '맑은 고딕'; color: #2D2D2D;"
    " background-color: #FFFFFF;"
    "}"
    "QLineEdit:focus, QTextEdit:focus {"
    " border: 1px solid #2E86AB;"
    "}"
)

_COMBO_QSS = """
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #DDE1E7;
    border-radius: 6px;
    padding: 6px 10px 6px 10px;
    color: #2D2D2D;
    font-family: '맑은 고딕';
    font-size: 10pt;
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
    outline: 0px;
    padding: 4px 0px;
    color: #2D2D2D;
    font-family: '맑은 고딕';
    font-size: 10pt;
}
QComboBox QAbstractItemView::item {
    min-height: 32px;
    padding: 6px 12px;
    background-color: #FFFFFF;
    color: #2D2D2D;
    border: none;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #F3F7FB;
    border: none;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #EAF3FB;
    color: #2D2D2D;
    border: none;
}
"""

_CAL_QSS = """
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


class _ComboArrowEventFilter(QObject):
    """콤보박스 크기 변경 시 ▾ 오버레이 위치를 유지한다."""

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            arrow = getattr(watched, "_arrow_label", None)
            if arrow is not None:
                arrow.move(watched.width() - 18, (watched.height() - 16) // 2)
        return super().eventFilter(watched, event)


_COMBO_ARROW_FILTER = _ComboArrowEventFilter()


def _make_combo(items: list[str] | None = None) -> QComboBox:
    """공통 콤보박스 팩토리 — 폰트·QSS·팝업 처리 일괄 적용."""
    combo = QComboBox()
    combo.setFont(_FONT)
    combo.setStyleSheet(_COMBO_QSS)
    combo.setMinimumWidth(160)
    combo.setFixedHeight(34)
    combo.setItemDelegate(QStyledItemDelegate(combo))

    if items:
        for item in items:
            combo.addItem(item)

    combo.setMaxVisibleItems(8)
    setup_combo(combo)
    _attach_combo_arrow(combo)
    return combo


def setup_combo(combo: QComboBox) -> None:
    """드롭다운 검은 배경/외곽선 이슈 방지용 공통 팝업 스타일."""
    view = QListView()
    view.setFont(_FONT)
    view.setStyleSheet(
        """
        QListView {
            background-color: #FFFFFF;
            border: 1px solid #DDE1E7;
            outline: none;
            color: #2D2D2D;
            font-family: '맑은 고딕';
            font-size: 10pt;
        }
        QListView::item {
            height: 32px;
            padding-left: 10px;
            background-color: #FFFFFF;
            border: none;
        }
        QListView::item:hover {
            background-color: #F0F2F5;
        }
        QListView::item:selected {
            background-color: #EBF5FB;
            color: #2E86AB;
        }
        """
    )
    combo.setView(view)
    view.window().setWindowFlags(
        Qt.WindowType.Popup
        | Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.NoDropShadowWindowHint
    )
    view.window().setStyleSheet("background-color: #FFFFFF; border: none;")
    view.viewport().setStyleSheet("background-color: #FFFFFF; border: none;")


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


class CaseCreateDialog(QDialog):
    def __init__(self, parent=None, prefill: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("새 사건 등록")
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setFont(_FONT)
        self.setStyleSheet(
            "QDialog { background-color: #FFFFFF;"
            " font-family: '맑은 고딕'; font-size: 10pt; }"
            + _FIELD_QSS
        )
        self._base_height = 460
        self._selected_date = QDate.currentDate()
        self._prefill = prefill or {}
        self._build_ui()
        self._load_clients()
        self._load_office_defaults()
        if self._prefill:
            self._apply_prefill(self._prefill)
        self.resize(480, self._base_height)  # 달력 숨김 상태 기본 높이

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(0)

        # ── 헤더 ──────────────────────────────────────
        title = QLabel("새 사건 등록")
        title.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #1B2A3B;"
            " background: transparent;"
        )
        root.addWidget(title)
        root.addSpacing(10)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #DDE1E7; max-height: 1px; border: none;")
        root.addWidget(sep)
        root.addSpacing(14)

        # ── 폼 ────────────────────────────────────────
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        def lbl(text: str) -> QLabel:
            l = QLabel(text)
            l.setFont(_FONT)
            l.setStyleSheet("color: #2D2D2D; font-size: 10pt; background: transparent;")
            return l

        # 납세자명
        self.payer_input = QLineEdit()
        self.payer_input.setPlaceholderText("예: 주식회사 케이뱅크")
        form.addRow(lbl("납세자명 *"), self.payer_input)

        # 납부일 — 인라인 달력
        date_row_widget = QWidget()
        date_row_widget.setStyleSheet("background: transparent;")
        date_h = QHBoxLayout(date_row_widget)
        date_h.setContentsMargins(0, 0, 0, 0)
        date_h.setSpacing(4)

        self.date_line = QLineEdit()
        self.date_line.setReadOnly(True)
        self.date_line.setText(self._selected_date.toString("yyyy-MM-dd"))
        self.date_line.setStyleSheet(
            "QLineEdit {"
            " border: 1px solid #DDE1E7; border-radius: 6px;"
            " padding: 6px 10px; font-size: 10pt;"
            " font-family: '맑은 고딕'; color: #2D2D2D;"
            " background-color: #F8F9FA;"
            "}"
        )

        btn_cal = QPushButton("📅")
        btn_cal.setFixedWidth(38)
        btn_cal.setCursor(Qt.PointingHandCursor)
        btn_cal.setStyleSheet(
            "QPushButton {"
            " background-color: #F0F2F5; border: 1px solid #DDE1E7;"
            " border-radius: 6px; font-size: 12pt;"
            "}"
            "QPushButton:hover { background-color: #DDE1E7; }"
        )

        date_h.addWidget(self.date_line)
        date_h.addWidget(btn_cal)

        # 인라인 달력 — 컨테이너 QWidget show/hide 방식
        cal = QCalendarWidget()
        cal.setGridVisible(False)
        cal.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        cal.setSelectedDate(self._selected_date)
        cal.setStyleSheet(_CAL_QSS)

        self.cal_container = QWidget()
        self._calendar_height = 220
        self.cal_container.setFixedHeight(self._calendar_height)
        cal_policy = QSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        cal_policy.setRetainSizeWhenHidden(False)
        self.cal_container.setSizePolicy(cal_policy)
        container_layout = QVBoxLayout(self.cal_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(cal)

        self.cal_widget = cal  # _apply_prefill 등에서 참조
        self._form_layout = form
        form.addRow(lbl("납부일 *"), date_row_widget)
        self._calendar_row_label = QLabel("")
        self._calendar_row_label.setStyleSheet("background: transparent;")
        form.addRow(self._calendar_row_label, self.cal_container)
        self._calendar_row_index = form.rowCount() - 1
        self._hide_calendar()

        def toggle_calendar():
            if self.cal_container.isVisible():
                self._hide_calendar()
            else:
                self._show_calendar()

        def on_date_selected(date: QDate):
            self._selected_date = date
            self.date_line.setText(date.toString("yyyy-MM-dd"))
            self._hide_calendar()

        btn_cal.clicked.connect(toggle_calendar)
        cal.clicked.connect(on_date_selected)

        # 세액
        self.tax_input = QLineEdit()
        self.tax_input.setPlaceholderText("예: 1,000,000")
        self.tax_input.textChanged.connect(self._format_tax)
        form.addRow(lbl("세액 *"), self.tax_input)

        # 환급사유
        self.reason_combo = _make_combo(REFUND_REASONS)
        self.reason_combo.setMaxVisibleItems(4)
        form.addRow(lbl("환급사유"), self.reason_combo)

        # 거래처
        self.client_combo = _make_combo()
        self.client_combo.addItem("(선택 안함)", None)
        form.addRow(lbl("거래처"), self.client_combo)

        # 담당자
        self.handler_input = QLineEdit()
        self.handler_input.setPlaceholderText("담당 법무사/직원명")
        form.addRow(lbl("담당자"), self.handler_input)

        # 메모
        self.memo_input = QTextEdit()
        self.memo_input.setFixedHeight(58)
        self.memo_input.setPlaceholderText("메모 (선택)")
        form.addRow(lbl("메모"), self.memo_input)

        root.addLayout(form)

        # ── 버튼 (하단 고정) ──────────────────────────
        root.addSpacing(16)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        btn_cancel = QPushButton("취소")
        btn_cancel.setFixedSize(90, 38)
        btn_cancel.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #2D2D2D;"
            " border: 1px solid #DDE1E7; border-radius: 6px;"
            " font-size: 10pt; font-family: '맑은 고딕'; }"
            "QPushButton:hover { background: #F0F2F5; }"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("등록")
        btn_ok.setFixedSize(90, 38)
        btn_ok.setStyleSheet(
            "QPushButton { background: #2E86AB; color: #FFFFFF;"
            " border: none; border-radius: 6px; font-weight: bold;"
            " font-size: 10pt; font-family: '맑은 고딕'; }"
            "QPushButton:hover { background: #2471A3; }"
        )
        btn_ok.clicked.connect(self._on_ok)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        root.addLayout(btn_row)

    def _show_calendar(self):
        self.cal_container.setFixedHeight(self._calendar_height)
        self.cal_container.show()
        self._form_layout.setRowVisible(self._calendar_row_index, True)
        expanded = max(self.height(), self._base_height + self._calendar_height + 14)
        self.resize(self.width(), expanded)

    def _hide_calendar(self):
        self.cal_container.hide()
        self.cal_container.setFixedHeight(0)
        self._form_layout.setRowVisible(self._calendar_row_index, False)
        QTimer.singleShot(0, self._restore_collapsed_height)

    def _restore_collapsed_height(self):
        self.resize(self.width(), self._base_height)

    # ── 데이터 로드 ──────────────────────────────────

    def _load_clients(self):
        try:
            from app.services.client_service import list_clients
            for c in list_clients():
                self.client_combo.addItem(c.client_name, c.id)
        except Exception:
            pass

    def _load_office_defaults(self):
        try:
            from app.services.office_info_service import get_office_value
            handler = get_office_value("사무소_법무사", "")
            if handler:
                self.handler_input.setText(handler)
        except Exception:
            pass

    def _apply_prefill(self, prefill: dict):
        payer = str(prefill.get("payer_name", "") or "").strip()
        if payer:
            self.payer_input.setText(payer)

        paid_date = prefill.get("paid_date")
        selected = None
        if isinstance(paid_date, QDate):
            selected = paid_date
        elif isinstance(paid_date, str):
            parsed = QDate.fromString(paid_date, "yyyy-MM-dd")
            if parsed.isValid():
                selected = parsed
        if selected and selected.isValid():
            self._selected_date = selected
            self.date_line.setText(selected.toString("yyyy-MM-dd"))
            self.cal_widget.setSelectedDate(selected)

        tax_total = prefill.get("tax_total")
        if tax_total not in (None, ""):
            self.tax_input.setText(str(tax_total))

        reason = str(prefill.get("refund_reason", "") or "").strip()
        if reason:
            idx = self.reason_combo.findText(reason)
            if idx < 0:
                self.reason_combo.addItem(reason)
                idx = self.reason_combo.findText(reason)
            if idx >= 0:
                self.reason_combo.setCurrentIndex(idx)

        client_id = prefill.get("client_id")
        if client_id is not None:
            idx = self.client_combo.findData(client_id)
            if idx >= 0:
                self.client_combo.setCurrentIndex(idx)

        handler = prefill.get("handler")
        if handler is not None:
            self.handler_input.setText(str(handler))

        memo = prefill.get("memo")
        if memo is not None:
            self.memo_input.setPlainText(str(memo))

    # ── 세액 콤마 포맷 ───────────────────────────────

    def _format_tax(self, text: str):
        digits = "".join(c for c in text if c.isdigit())
        formatted = f"{int(digits):,}" if digits else ""
        if self.tax_input.text() != formatted:
            self.tax_input.blockSignals(True)
            self.tax_input.setText(formatted)
            self.tax_input.blockSignals(False)

    def _tax_int(self) -> int:
        digits = "".join(c for c in self.tax_input.text() if c.isdigit())
        return int(digits) if digits else 0

    # ── 등록 처리 ────────────────────────────────────

    def _on_ok(self):
        payer = self.payer_input.text().strip()
        paid_date = self._selected_date.toString("yyyy-MM-dd")
        tax = self._tax_int()

        if not payer:
            QMessageBox.warning(self, "입력 오류", "납세자명을 입력하세요.")
            self.payer_input.setFocus()
            return
        if tax <= 0:
            QMessageBox.warning(self, "입력 오류", "세액을 올바르게 입력하세요.")
            self.tax_input.setFocus()
            return

        try:
            from app.services.case_service import create_case
            create_case(
                payer_name=payer,
                paid_date=paid_date,
                tax_total=tax,
                refund_reason=self.reason_combo.currentText(),
                client_id=self.client_combo.currentData(),
                handler=self.handler_input.text().strip() or None,
                memo=self.memo_input.toPlainText().strip() or None,
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", str(e))
