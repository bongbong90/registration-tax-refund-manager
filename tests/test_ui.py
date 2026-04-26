"""
UI 기본 동작 확인.
창이 정상적으로 뜨는지만 확인.

사용:
    python -m tests.test_ui
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow

QSS_PATH = Path(__file__).parent.parent / "app" / "ui" / "styles" / "theme.qss"


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.load_stylesheet(str(QSS_PATH))
    window.show()

    print("✓ 메인 창 정상 실행")
    print("  창을 닫으면 테스트 종료됩니다.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
