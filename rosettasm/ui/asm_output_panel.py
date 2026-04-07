from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtGui import QFont, QColor, QTextFormat
from PyQt6.QtCore import pyqtSignal, Qt


class AssemblyTextEdit(QTextEdit):
    up_pressed = pyqtSignal()
    down_pressed = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self.up_pressed.emit()
            return

        if event.key() == Qt.Key.Key_Down:
            self.down_pressed.emit()
            return

        super().keyPressEvent(event)


class AsmOutputPanel(QFrame):
    line_selected = pyqtSignal(int)

    def __init__(self, title: str = "Assembly Output"):
        super().__init__()

        self.current_line_index = 0

        self.setFrameShape(QFrame.Shape.Box)
        self._build_ui(title)
        self._connect_signals()

    def _build_ui(self, title: str):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        top_bar = QHBoxLayout()

        label = QLabel(title)
        label.setFont(QFont("DM Serif Display", 12))

        self.prev_button = QPushButton("<<Prev")
        self.next_button = QPushButton("Next>>")

        button_font = QFont("DM Serif Display", 11)
        self.prev_button.setFont(button_font)
        self.next_button.setFont(button_font)

        self.prev_button.setFixedHeight(28)
        self.next_button.setFixedHeight(28)

        top_bar.addWidget(label)
        top_bar.addStretch()
        top_bar.addWidget(self.prev_button)
        top_bar.addWidget(self.next_button)

        self.asm_output = AssemblyTextEdit()
        self.asm_output.setFont(QFont("Consolas", 12))
        self.asm_output.setReadOnly(True)

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.asm_output)

        self.setLayout(main_layout)

    def _connect_signals(self):
        self.asm_output.cursorPositionChanged.connect(self._emit_selected_line)
        self.asm_output.up_pressed.connect(self._handle_up_pressed)
        self.asm_output.down_pressed.connect(self._handle_down_pressed)

    def _handle_up_pressed(self):
        if self.current_line_index > 0:
            self.line_selected.emit(self.current_line_index - 1)

    def _handle_down_pressed(self):
        block_count = self.asm_output.document().blockCount()
        if self.current_line_index < block_count - 1:
            self.line_selected.emit(self.current_line_index + 1)

    def _emit_selected_line(self):
        line_index = self.get_current_line_index()

        if line_index != self.current_line_index:
            self.current_line_index = line_index
            self.line_selected.emit(line_index)

    def set_assembly_text(self, asm_lines: list[str]):
        self.asm_output.setPlainText("\n".join(asm_lines))
        self.current_line_index = -1
        self.clear_highlight()

    def highlight_line(self, index: int):
        self.current_line_index = index

        self.asm_output.blockSignals(True)

        cursor = self.asm_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.movePosition(
            cursor.MoveOperation.Down,
            cursor.MoveMode.MoveAnchor,
            index
        )
        self.asm_output.setTextCursor(cursor)

        selection = QTextEdit.ExtraSelection()
        selection.cursor = cursor
        selection.cursor.clearSelection()
        selection.format.setBackground(QColor("#0A64F0"))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)

        self.asm_output.setExtraSelections([selection])
        self.asm_output.ensureCursorVisible()

        self.asm_output.blockSignals(False)

    def clear_highlight(self):
        self.current_line_index = -1
        self.asm_output.blockSignals(True)
        cursor = self.asm_output.textCursor()
        cursor.clearSelection()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.asm_output.setTextCursor(cursor)
        self.asm_output.setExtraSelections([])
        self.asm_output.blockSignals(False)

    def get_current_line_index(self) -> int:
        return self.asm_output.textCursor().blockNumber()

    def connect_prev_clicked(self, callback):
        self.prev_button.clicked.connect(callback)

    def connect_next_clicked(self, callback):
        self.next_button.clicked.connect(callback)
