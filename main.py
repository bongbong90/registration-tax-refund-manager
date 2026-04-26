import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon

from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("맑은 고딕", 10))
    app.setWindowIcon(QIcon("assets/icons/app_icon.ico"))

    main_window = MainWindow()
    main_window.setWindowIcon(QIcon("assets/icons/app_icon.ico"))

    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
