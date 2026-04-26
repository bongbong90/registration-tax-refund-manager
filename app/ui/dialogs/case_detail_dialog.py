"""사건 상세 다이얼로그."""
from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QFont
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
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

REFUND_REASONS = ["대출취소", "중복납부", "착오납부", "기타"]
FONT = QFont("맑은 고딕", 10)


class CaseDetailDialog(QDialog):
    updated = Signal()

    def __init__(self, case_id: int, parent=None):
        super().__init__(parent)
        self.case_id = case_id
        self._status = "CREATED"

        self.setWindowTitle("사건 상세")
        self.setModal(True)
        self.resize(600, 700)
        self.setFont(FONT)
        self.setStyleSheet(
            "QDialog { background-color: #FFFFFF; font-family: '맑은 고딕'; }"
            "QLineEdit, QDateEdit, QTextEdit, QComboBox {"
            " border: 1px solid #DDE1E7; border-radius: 6px; padding: 6px 10px;"
            "}"
            "QPushButton#btn_primary {"
            " background-color: #2E86AB; color: #FFFFFF; border: none;"
            " border-radius: 6px; font-weight: bold; padding: 8px 14px;"
            "}"
            "QPushButton#btn_primary:hover { background-color: #2471A3; }"
            "QPushButton#btn_secondary {"
            " background-color: #FFFFFF; color: #2D2D2D;"
            " border: 1px solid #DDE1E7; border-radius: 6px; padding: 8px 14px;"
            "}"
            "QPushButton#btn_secondary:hover { background-color: #F0F2F5; }"
        )

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

    def _build_tab_basic(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        def lbl(text: str) -> QLabel:
            label = QLabel(text)
            label.setStyleSheet("color: #2D2D2D;")
            return label

        self.payer_input = QLineEdit()
        form.addRow(lbl("납세자명"), self.payer_input)

        self.paid_date_edit = QDateEdit()
        self.paid_date_edit.setCalendarPopup(True)
        self.paid_date_edit.setDisplayFormat("yyyy-MM-dd")
        form.addRow(lbl("납부일"), self.paid_date_edit)

        self.tax_input = QLineEdit()
        self.tax_input.textChanged.connect(self._format_tax)
        form.addRow(lbl("세액"), self.tax_input)

        self.reason_combo = QComboBox()
        self.reason_combo.addItems(REFUND_REASONS)
        form.addRow(lbl("환급사유"), self.reason_combo)

        self.client_combo = QComboBox()
        self.client_combo.addItem("(선택 안함)", None)
        form.addRow(lbl("거래처"), self.client_combo)

        self.handler_input = QLineEdit()
        form.addRow(lbl("담당자"), self.handler_input)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save_basic = QPushButton("저장")
        btn_save_basic.setObjectName("btn_primary")
        btn_save_basic.clicked.connect(self._on_save_basic)
        btn_row.addWidget(btn_save_basic)
        layout.addLayout(btn_row)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #DDE1E7; max-height: 1px; border: none;")
        layout.addWidget(line)

        status_row = QHBoxLayout()
        self.status_label = QLabel("현재 상태: -")
        self.status_label.setStyleSheet("font-weight: bold; color: #2D2D2D;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()

        self.btn_next_status = QPushButton("다음 단계로")
        self.btn_next_status.setObjectName("btn_secondary")
        self.btn_next_status.clicked.connect(self._on_advance_status)
        status_row.addWidget(self.btn_next_status)
        layout.addLayout(status_row)
        layout.addStretch()

        self.tabs.addTab(tab, "기본정보")

    def _build_tab_history(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["처리일시", "내용", "처리자"])
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.history_table.setShowGrid(False)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.verticalHeader().setDefaultSectionSize(40)
        self.history_table.setStyleSheet(
            "QTableWidget { border: none; background-color: #FFFFFF; }"
            "QTableWidget::item { border-bottom: 1px solid #EEF2F6; padding: 8px; }"
            "QHeaderView::section {"
            " background-color: #F8F9FA; color: #7F8C8D; font-weight: bold;"
            " border: none; border-bottom: 1px solid #DDE1E7; padding: 8px;"
            "}"
        )

        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.history_table.setColumnWidth(0, 170)
        self.history_table.setColumnWidth(2, 120)

        layout.addWidget(self.history_table, stretch=1)
        self.tabs.addTab(tab, "진행이력")

    def _build_tab_memo(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.memo_edit = QTextEdit()
        layout.addWidget(self.memo_edit, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save = QPushButton("저장")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self._on_save_memo)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        self.tabs.addTab(tab, "메모")

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

        self._status = case.get("status", "CREATED") or "CREATED"
        self.status_label.setText(f"현재 상태: {STATUS_LABELS.get(self._status, self._status)}")
        self.btn_next_status.setEnabled(self._status != "CLOSED")

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
            col2 = QTableWidgetItem(actor)
            col2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

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
                self._status = "CLOSED"
                self.status_label.setText(f"현재 상태: {STATUS_LABELS['CLOSED']}")
                self.btn_next_status.setEnabled(False)
                QMessageBox.information(self, "안내", "이미 종결 상태입니다.")
                return

            self._status = next_status
            self.status_label.setText(f"현재 상태: {STATUS_LABELS.get(next_status, next_status)}")
            self.btn_next_status.setEnabled(next_status != "CLOSED")
            self._load_history()
            self.updated.emit()
        except Exception as exc:
            QMessageBox.critical(self, "상태 변경 실패", str(exc))
