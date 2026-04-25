"""거래처 관리 메인 창. 목록 + 검색 + CRUD 버튼."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from app.services.client_service import (
    list_clients,
    delete_client,
    get_client,
)
from app.utils.excel_io import export_to_excel, import_from_excel
from app.ui.client_edit_dialog import ClientEditDialog


class ClientManagerWindow(tk.Toplevel):
    """거래처 관리 창."""

    def __init__(self, parent=None):
        super().__init__(parent) if parent else super().__init__()

        self.title("거래처 관리")
        self.geometry("960x600")

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        # 상단 툴바
        toolbar = ttk.Frame(self, padding=8)
        toolbar.pack(fill="x")

        ttk.Label(toolbar, text="검색:").pack(side="left", padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._refresh())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(0, 12))

        ttk.Button(toolbar, text="추가", command=self._on_add).pack(side="left", padx=2)
        ttk.Button(toolbar, text="수정", command=self._on_edit).pack(side="left", padx=2)
        ttk.Button(toolbar, text="삭제", command=self._on_delete).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=8)

        ttk.Button(toolbar, text="엑셀 가져오기", command=self._on_import).pack(side="left", padx=2)
        ttk.Button(toolbar, text="엑셀 내보내기", command=self._on_export).pack(side="left", padx=2)

        # 목록 (Treeview)
        list_frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        list_frame.pack(fill="both", expand=True)

        columns = (
            "client_name",
            "corporation_no",
            "representative_name",
            "manager_name",
            "manager_phone",
        )
        column_labels = {
            "client_name": "거래처명",
            "corporation_no": "법인등록번호",
            "representative_name": "대표자",
            "manager_name": "담당자",
            "manager_phone": "담당자전화",
        }
        column_widths = {
            "client_name": 220,
            "corporation_no": 140,
            "representative_name": 120,
            "manager_name": 100,
            "manager_phone": 130,
        }

        self.tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", selectmode="browse"
        )
        for col in columns:
            self.tree.heading(col, text=column_labels[col])
            self.tree.column(col, width=column_widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 더블클릭 = 수정
        self.tree.bind("<Double-1>", lambda e: self._on_edit())

        # 상태바
        self.status_var = tk.StringVar(value="준비")
        status = ttk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",
            relief="sunken",
            padding=4,
        )
        status.pack(fill="x", side="bottom")

    def _refresh(self):
        # 기존 항목 클리어
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 데이터 로드
        search = self.search_var.get().strip()
        clients = list_clients(search=search)

        for c in clients:
            self.tree.insert(
                "",
                "end",
                iid=str(c.id),
                values=(
                    c.client_name,
                    c.corporation_no or "",
                    c.representative_name or "",
                    c.manager_name or "",
                    c.manager_phone or "",
                ),
            )

        self.status_var.set(f"전체 {len(clients)}건")

    def _get_selected_id(self) -> int | None:
        sel = self.tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _on_add(self):
        ClientEditDialog(self, client_id=None, on_saved=lambda _: self._refresh())

    def _on_edit(self):
        client_id = self._get_selected_id()
        if not client_id:
            messagebox.showinfo("선택 필요", "수정할 거래처를 선택하세요.")
            return
        ClientEditDialog(self, client_id=client_id, on_saved=lambda _: self._refresh())

    def _on_delete(self):
        client_id = self._get_selected_id()
        if not client_id:
            messagebox.showinfo("선택 필요", "삭제할 거래처를 선택하세요.")
            return

        client = get_client(client_id)
        if not client:
            return

        if not messagebox.askyesno("삭제 확인", f"'{client.client_name}'을(를) 삭제하시겠습니까?"):
            return

        try:
            delete_client(client_id)
            self._refresh()
        except Exception as e:
            messagebox.showerror("삭제 실패", str(e))

    def _on_export(self):
        file_path = filedialog.asksaveasfilename(
            title="거래처 엑셀로 내보내기",
            defaultextension=".xlsx",
            filetypes=[("Excel 파일", "*.xlsx")],
            initialfile="거래처마스터.xlsx",
        )
        if not file_path:
            return

        try:
            count = export_to_excel(Path(file_path))
            messagebox.showinfo("완료", f"{count}건 내보내기 완료\n{file_path}")
        except Exception as e:
            messagebox.showerror("내보내기 실패", str(e))

    def _on_import(self):
        file_path = filedialog.askopenfilename(
            title="거래처 엑셀 가져오기",
            filetypes=[("Excel 파일", "*.xlsx *.xls")],
        )
        if not file_path:
            return

        if not messagebox.askyesno(
            "가져오기 확인",
            "엑셀에서 거래처를 가져옵니다.\n"
            "동일 거래처명은 업데이트되고, 새 거래처는 추가됩니다.\n계속하시겠습니까?",
        ):
            return

        try:
            result = import_from_excel(Path(file_path))
            msg = f"신규: {result['created']}건\n수정: {result['updated']}건\n스킵: {result['skipped']}건"
            if result["errors"]:
                msg += f"\n\n오류:\n" + "\n".join(result["errors"][:10])
                if len(result["errors"]) > 10:
                    msg += f"\n... 외 {len(result['errors']) - 10}건"
            messagebox.showinfo("가져오기 완료", msg)
            self._refresh()
        except Exception as e:
            messagebox.showerror("가져오기 실패", str(e))
