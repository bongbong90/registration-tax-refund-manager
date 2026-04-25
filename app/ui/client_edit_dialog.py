"""거래처 추가/수정 다이얼로그."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable

from app.services.client_service import (
    create_client,
    update_client,
    get_client,
)
from app.ui.components.form_fields import LabeledEntry, LabeledText


class ClientEditDialog(tk.Toplevel):
    """거래처 추가/수정 모달 다이얼로그."""

    def __init__(
        self,
        parent,
        client_id: Optional[int] = None,
        on_saved: Optional[Callable[[int], None]] = None,
    ):
        super().__init__(parent)
        self.client_id = client_id
        self.on_saved = on_saved

        self.title("거래처 수정" if client_id else "거래처 추가")
        self.geometry("560x520")
        self.transient(parent)
        self.grab_set()

        self._build_ui()

        if client_id:
            self._load_data()

    def _build_ui(self):
        main = ttk.Frame(self, padding=16)
        main.pack(fill="both", expand=True)

        self.fields = {}

        # 필수
        self.fields["client_name"] = LabeledEntry(main, "거래처명", required=True)
        self.fields["client_name"].pack(fill="x", pady=4)

        # 등록번호류
        self.fields["corporation_no"] = LabeledEntry(main, "법인등록번호")
        self.fields["corporation_no"].pack(fill="x", pady=4)

        self.fields["business_no"] = LabeledEntry(main, "사업자등록번호")
        self.fields["business_no"].pack(fill="x", pady=4)

        self.fields["representative_name"] = LabeledEntry(main, "대표자")
        self.fields["representative_name"].pack(fill="x", pady=4)

        self.fields["address"] = LabeledEntry(main, "주소", width=60)
        self.fields["address"].pack(fill="x", pady=4)

        self.fields["email"] = LabeledEntry(main, "이메일")
        self.fields["email"].pack(fill="x", pady=4)

        # 담당자
        ttk.Separator(main).pack(fill="x", pady=8)

        self.fields["manager_name"] = LabeledEntry(main, "담당자명")
        self.fields["manager_name"].pack(fill="x", pady=4)

        self.fields["manager_phone"] = LabeledEntry(main, "담당자전화")
        self.fields["manager_phone"].pack(fill="x", pady=4)

        # 메모
        ttk.Separator(main).pack(fill="x", pady=8)

        self.fields["memo"] = LabeledText(main, "비고", height=3)
        self.fields["memo"].pack(fill="both", expand=True, pady=4)

        # 버튼
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(12, 0))

        ttk.Button(btn_frame, text="저장", command=self._save).pack(side="right", padx=4)
        ttk.Button(btn_frame, text="취소", command=self.destroy).pack(side="right")

    def _load_data(self):
        client = get_client(self.client_id)
        if not client:
            messagebox.showerror("오류", "거래처를 찾을 수 없습니다.")
            self.destroy()
            return

        for key, field in self.fields.items():
            value = getattr(client, key, None)
            field.set(value)

    def _save(self):
        # 필수 검증
        if not self.fields["client_name"].is_valid():
            messagebox.showwarning("입력 오류", "거래처명은 필수입니다.")
            return

        # 데이터 수집
        data = {key: field.get() or None for key, field in self.fields.items()}

        try:
            if self.client_id:
                update_client(self.client_id, **data)
                saved_id = self.client_id
            else:
                saved_id = create_client(**data)

            if self.on_saved:
                self.on_saved(saved_id)

            self.destroy()
        except Exception as e:
            messagebox.showerror("저장 실패", str(e))
