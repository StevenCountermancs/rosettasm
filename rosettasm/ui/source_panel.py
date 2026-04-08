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
    #############################################################################
    # Function name:        __init__                                            #
    # Description:          Initializes the source code panel                   #
    # Parameters:    str –  title: title displayed at the top of the panel      #
    # Return Value: None                                                        #
    #############################################################################
    def __init__(self, title: str = "Source Code"):
        super().__init__()

        self.current_highlighted_lines = set()
        self.source_line_marker = 0

        self.setFrameShape(QFrame.Shape.Box)
        self._build_ui(title)

    #############################################################################
    # Function name:        _build_ui                                           #
    # Description:          Builds the widgets and layout for the panel         #
    # Parameters:    str –  title: title displayed at the top of the panel      #
    # Return Value: None                                                        #
    #############################################################################
    def _build_ui(self, title: str):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        top_bar = QHBoxLayout()

        label = QLabel(title)
        label.setFont(QFont("DM Serif Display", 12))
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

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

    #############################################################################
    # Function name:        _configure_editor                                   #
    # Description:          Configures the source editor appearance and behavior#
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
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

    #############################################################################
    # Function name:        get_source_code                                     #
    # Description:          Retrieves the current source code from the editor   #
    # Parameters:    None                                                       #
    # Return Value: str – source code currently in the editor                   #
    #############################################################################
    def get_source_code(self) -> str:
        return self.editor.text()

    #############################################################################
    # Function name:        set_source_code                                     #
    # Description:          Replaces the editor contents with source code       #
    # Parameters:    str –  text: source code to place in the editor            #
    # Return Value: None                                                        #
    #############################################################################
    def set_source_code(self, text: str):
        self.editor.setText(text)

    #############################################################################
    # Function name:        highlight_source_lines                              #
    # Description:          Highlights multiple source lines in the editor      #
    # Parameters:    list – line_indices: source line indices to highlight      #
    # Return Value: None                                                        #
    #############################################################################
    def highlight_source_lines(self, line_indices: list[int]):
        self.clear_source_highlight()

        for line_index in line_indices:
            if line_index >= 0:
                self.editor.markerAdd(line_index, self.source_line_marker)
                self.current_highlighted_lines.add(line_index)

    #############################################################################
    # Function name:        highlight_source_line                               #
    # Description:          Highlights a single source line in the editor       #
    # Parameters:    int –  line_index: source line index to highlight          #
    # Return Value: None                                                        #
    #############################################################################
    def highlight_source_line(self, line_index: int):
        self.highlight_source_lines([line_index])

    #############################################################################
    # Function name:        clear_source_highlight                              #
    # Description:          Clears all highlighted source lines                 #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def clear_source_highlight(self):
        for line_index in self.current_highlighted_lines:
            self.editor.markerDelete(line_index, self.source_line_marker)
        self.current_highlighted_lines.clear()