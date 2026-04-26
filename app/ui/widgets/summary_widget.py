from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
)
from PySide6.QtCore import Qt


class SummaryWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value_labels: dict[str, QLabel] = {}
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("ProgressCard")
        self.setFixedHeight(154)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAutoFillBackground(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(
            "#ProgressCard {"
            " background-color: #223D59;"
            " border: 1px solid #35506A;"
            " border-radius: 12px;"
            "}"
            "#ProgressCard QLabel {"
            " background: transparent;"
            " border: none;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(13, 12, 13, 12)
        layout.setSpacing(8)

        header = QLabel("진행 현황")
        header.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        header.setAutoFillBackground(False)
        header.setStyleSheet(
            "color: #FFFFFF;"
            " font-weight: bold;"
            " font-size: 10.5pt;"
            " background: transparent;"
        )
        layout.addWidget(header)

        line = QFrame()
        line.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        line.setAutoFillBackground(False)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(
            "background-color: #35506A;"
            " min-height: 1px;"
            " max-height: 1px;"
            " border: none;"
        )
        layout.addWidget(line)

        def make_row(label_text: str, badge_color: str) -> tuple[QWidget, QLabel]:
            row = QWidget()
            row.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            row.setAutoFillBackground(False)
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            row.setMinimumHeight(27)

            label = QLabel(label_text)
            label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            label.setAutoFillBackground(False)
            label.setStyleSheet(
                "color: #D8E2EC;"
                " font-size: 9.5pt;"
                " background: transparent;"
            )

            badge = QLabel("0")
            badge.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            badge.setAutoFillBackground(False)
            badge.setFixedSize(28, 22)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                f"background-color: {badge_color};"
                " color: #FFFFFF;"
                " font-weight: bold;"
                " font-size: 9pt;"
                " border-radius: 11px;"
                " border: 1px solid rgba(255,255,255,0.18);"
            )

            row_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(badge)
            return row, badge

        row_all, badge_all = make_row("전체", "#2F5373")
        row_ing, badge_ing = make_row("진행중", "#2E86AB")
        row_done, badge_done = make_row("완료", "#2F5373")

        layout.addWidget(row_all)
        layout.addWidget(row_ing)
        layout.addWidget(row_done)

        self._value_labels["total"] = badge_all
        self._value_labels["in_progress"] = badge_ing
        self._value_labels["closed"] = badge_done

    def update_summary(self, total: int, in_progress: int, closed: int):
        self._value_labels["total"].setText(str(total))
        self._value_labels["in_progress"].setText(str(in_progress))
        self._value_labels["closed"].setText(str(closed))
