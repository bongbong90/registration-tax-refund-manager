from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QStackedWidget, QStatusBar, QLabel
)
from PySide6.QtCore import Qt, QDate

from app.ui.widgets.sidebar import SidebarWidget
from app.ui.widgets.case_table import CaseTableWidget
from app.ui.styles.theme import get_stylesheet
from app.db.migrations import init_database


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("등록면허세 환급관리")
        self.resize(1280, 780)
        self.setMinimumSize(1024, 600)

        init_database()
        self.setStyleSheet(get_stylesheet())
        self._build_ui()
        self._connect_signals()
        self.sidebar.set_active("refund")
        self._refresh()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = SidebarWidget()
        root.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, stretch=1)

        # 페이지 0: 환급관리 (사건 목록)
        self.case_page = CaseTableWidget()
        self.stack.addWidget(self.case_page)

        # 페이지 1: 사건 관리 (준비 중)
        self.stack.addWidget(self._placeholder("사건 관리"))

        # 페이지 2: 거래처 관리 (준비 중)
        self.stack.addWidget(self._placeholder("거래처 관리"))

        # 페이지 3: 사무소 정보 (준비 중)
        self.stack.addWidget(self._placeholder("사무소 정보"))

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비")

    def _placeholder(self, text: str) -> QLabel:
        lbl = QLabel(f"{text}\n(다음 단계에서 구현)")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            "color: #7F8C8D; font-size: 12pt; font-family: '맑은 고딕';"
        )
        return lbl

    def _connect_signals(self):
        self.sidebar.menu_clicked.connect(self._on_menu)
        self.case_page.case_selected.connect(self._on_case_selected)
        self.case_page.add_requested.connect(self._on_add_case)
        self.case_page.copy_requested.connect(self._on_copy_case)

    _PAGE_MAP = {"refund": 0, "cases": 1, "clients": 2, "office": 3}
    _LABEL_MAP = {
        "refund": "환급관리",
        "cases": "사건 관리",
        "clients": "거래처 관리",
        "office": "사무소 정보",
    }

    def _on_menu(self, key: str):
        self.stack.setCurrentIndex(self._PAGE_MAP.get(key, 0))
        self.status_bar.showMessage(self._LABEL_MAP.get(key, ""))

    def _refresh(self):
        """사건 목록 + 진행현황 배지 갱신."""
        self.case_page.refresh_from_db()
        try:
            from app.services.case_service import get_case_stats
            stats = get_case_stats()
            self.sidebar.summary.update_summary(
                total=stats["total"],
                in_progress=stats["in_progress"],
                closed=stats["closed"],
            )
        except Exception:
            pass

    def _on_case_selected(self, case_id: int):
        from app.ui.dialogs.case_detail_dialog import CaseDetailDialog

        dlg = CaseDetailDialog(case_id, self)
        dlg.updated.connect(self._refresh)
        dlg.exec()
        self.status_bar.showMessage(f"사건 {case_id} 상세 확인")

    def _on_add_case(self):
        if self._open_case_create_dialog():
            self.status_bar.showMessage("새 사건이 등록됐습니다.")

    def _on_copy_case(self, case_id: int):
        from app.services.case_service import get_case

        source = get_case(case_id)
        if not source:
            self.status_bar.showMessage("복사할 사건을 찾지 못했습니다.")
            return

        prefill = {
            "payer_name": source.get("payer_name", ""),
            "paid_date": QDate.currentDate().toString("yyyy-MM-dd"),
            "tax_total": source.get("tax_total", ""),
            "refund_reason": source.get("refund_reason", ""),
            "client_id": source.get("client_id"),
            "handler": source.get("handler", ""),
            "memo": source.get("memo", ""),
        }
        if self._open_case_create_dialog(prefill=prefill):
            self.status_bar.showMessage("사건 복사본이 등록됐습니다.")

    def _open_case_create_dialog(self, prefill: dict | None = None) -> bool:
        from app.ui.dialogs.case_create_dialog import CaseCreateDialog
        from PySide6.QtWidgets import QDialog

        dlg = CaseCreateDialog(self, prefill=prefill)
        if dlg.exec() == QDialog.Accepted:
            self._refresh()
            return True
        return False
