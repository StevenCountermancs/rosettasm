from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)
from PyQt6.QtCore import Qt
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtGui import QFont, QColor

class SourcePanel(QFrame):
    def __init__(self, title: str = "Source Code"):
        super().__init__()

        self.current_highlighted_line = -1
        self.source_line_marker = 0

        self.setFrameShape(QFrame.Shape.Box)
        self._build_ui(title)

    def _build_ui(self, title: str):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        top_bar = QHBoxLayout()

        label = QLabel(title)
        label.setFont(QFont("DM Serif Display", 12))
        label.setAlignment(Qt.AlignmentFlag.AlignLeft| Qt. AlignmentFlag.AlignTop)

        self.run_button = QPushButton("▶ Run")
        self.run_button.setFont(QFont("DM Serif Display", 12))
        self.run_button.setFixedHeight(28)

        top_bar.addWidget(label)
        top_bar.addStretch()
        top_bar.addWidget(self.run_button)

        self.editor = QsciScintilla()
        self._configure_editor()

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.editor)

        self.setLayout(main_layout)

    def _configure_editor(self):
        self.editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.editor.setMarginWidth(0, "0000")
        self.editor.setMarginsBackgroundColor(QColor("#252526"))
        self.editor.setMarginsForegroundColor(QColor("#aaaaaa"))
        self.editor.setIndentationsUseTabs(False)
        self.editor.setTabWidth(4)
        self.editor.setIndentationWidth(4)
        self.editor.setAutoIndent(True)
        self.editor.setBackspaceUnindents(True)
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QColor("#1e1e1e"))
        self.editor.setCaretForegroundColor(QColor("white"))
        self.editor.setEdgeMode(QsciScintilla.EdgeMode.EdgeNone)

        font = QFont("Consolas", 12)
        self.editor.setFont(font)
        self.editor.setMarginsFont(font)

        self.editor.markerDefine(QsciScintilla.MarkerSymbol.Background, self.source_line_marker)
        self.editor.setMarkerBackgroundColor(QColor("#0A64F0"), self.source_line_marker)

    def get_source_code(self) -> str:
        return self.editor.text()
    
    def set_source_code(self, text: str):
        self.editor.setText(text)

    def highlight_source_line(self, line_index: int):
        self.clear_source_highlight()

        if line_index < 0:
            return
        
        self.editor.markerAdd(line_index, self.source_line_marker)
        self.current_highlighted_line = line_index

    def clear_source_highlight(self):
        if self.current_highlighted_line >= 0:
            self.editor.markerDelete(self.current_highlighted_line, self.source_line_marker)
            self.current_highlighted_line = -1