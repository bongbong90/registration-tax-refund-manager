"""
등록면허세 환급관리 프로그램 엔트리포인트.
Phase 1-2 단계: DB 초기화 + 거래처 관리 GUI.
사건 관리는 Phase 1-4에서 추가됨.
"""
import tkinter as tk
from app.db.migrations import init_database
from app.ui.client_manager_window import ClientManagerWindow


def main():
    # DB 초기화 (이미 있으면 스킵)
    init_database()

    # 임시: 거래처 관리 창을 메인으로 띄움
    # Phase 1-4에서 사건 관리 메인 창으로 교체됨
    root = tk.Tk()
    root.withdraw()  # 메인 윈도우 숨김

    win = ClientManagerWindow(root)
    win.protocol("WM_DELETE_WINDOW", root.quit)

    root.mainloop()


if __name__ == "__main__":
    main()
