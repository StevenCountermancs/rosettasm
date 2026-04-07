from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QTextEdit,
)
from PyQt6.QtGui import QFont

class TerminalPanel(QFrame):
    def __init__(self, title: str = "Terminal"):
        super().__init__()

        self.setFrameShape(QFrame.Shape.Box)
        self._build_ui(title)

    def _build_ui(self, title: str):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setFont(QFont("DM Serif Display", 12))

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 11))

        layout.addWidget(title_label)
        layout.addWidget(self.output)

        self.setLayout(layout)

    def set_text(self, text: str):
        self.output.setPlainText(text)

    def append_text(self, text: str):
        self.output.append(text)

    def clear_output(self):
        self.output.clear()

    def show_error(self, message: str):
        self.output.setPlainText(f"Error: {message}")