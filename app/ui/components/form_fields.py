"""tkinter 공통 폼 위젯."""
import tkinter as tk
from tkinter import ttk
from typing import Optional


class LabeledEntry(ttk.Frame):
    """라벨 + 입력 필드 한 줄."""

    def __init__(self, parent, label: str, width: int = 40, required: bool = False):
        super().__init__(parent)

        label_text = f"{label} *" if required else label
        self.label = ttk.Label(self, text=label_text, width=15, anchor="w")
        self.label.pack(side="left", padx=(0, 8))

        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.pack(side="left", fill="x", expand=True)

        self.required = required

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: Optional[str]) -> None:
        self.var.set(value or "")

    def is_valid(self) -> bool:
        if self.required and not self.get():
            return False
        return True


class LabeledText(ttk.Frame):
    """라벨 + 멀티라인 텍스트 (메모 등)."""

    def __init__(self, parent, label: str, height: int = 4):
        super().__init__(parent)

        self.label = ttk.Label(self, text=label, width=15, anchor="nw")
        self.label.pack(side="left", padx=(0, 8), anchor="n")

        self.text = tk.Text(self, height=height, width=40, wrap="word")
        self.text.pack(side="left", fill="both", expand=True)

    def get(self) -> str:
        return self.text.get("1.0", "end").strip()

    def set(self, value: Optional[str]) -> None:
        self.text.delete("1.0", "end")
        if value:
            self.text.insert("1.0", value)
