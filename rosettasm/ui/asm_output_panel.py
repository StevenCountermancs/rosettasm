from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtGui import QFont, QColor, QTextFormat
from PyQt6.QtCore import pyqtSignal, Qt


class AssemblyTextEdit(QTextEdit):
    up_pressed = pyqtSignal()
    down_pressed = pyqtSignal()

#############################################################################
# Function name:        keyPressEvent                                       #
# Description:          Emits custom signals for up/down arrow key presses  #
# Parameters:    QKeyEvent – event: key press event from the text editor    #
# Return Value: None                                                        #
#############################################################################
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
    step_prev_requested = pyqtSignal()
    step_next_requested = pyqtSignal()

#############################################################################
# Function name:        __init__                                            #
# Description:          Initializes the assembly output panel               #
# Parameters:    str –  title: title displayed at the top of the panel      #
# Return Value: None                                                        #
#############################################################################
    def __init__(self, title: str = "Assembly Output"):
        super().__init__()

        self.current_line_index = 0
        self.display_to_real_index = []
        self.real_to_display_index = {}

        self.setFrameShape(QFrame.Shape.Box)
        self._build_ui(title)
        self._connect_signals()

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

#############################################################################
# Function name:        _connect_signals                                    #
# Description:          Connects widget signals to panel event handlers     #
# Parameters:    None                                                       #
# Return Value: None                                                        #
#############################################################################
    def _connect_signals(self):
        self.asm_output.cursorPositionChanged.connect(self._emit_selected_line)
        self.asm_output.up_pressed.connect(self._handle_up_pressed)
        self.asm_output.down_pressed.connect(self._handle_down_pressed)

#############################################################################
# Function name:        _handle_up_pressed                                  #
# Description:          Emits request to step to previous assembly line     #
# Parameters:   None                                                        #
# Return Value: None                                                        #
#############################################################################
    def _handle_up_pressed(self):
        self.step_prev_requested.emit()

#############################################################################
# Function name:        _handle_down_pressed                                #
# Description:          Emits request to step to next assembly line         #
# Parameters:    None                                                       #
# Return Value: None                                                        #
#############################################################################
    def _handle_down_pressed(self):
        self.step_next_requested.emit()

#############################################################################
# Function name:        _emit_selected_line                                 #
# Description:          Emits signal when a new assembly line is selected   #
# Parameters:    None                                                       #
# Return Value: None                                                        #
#############################################################################
    def _emit_selected_line(self):
        line_index = self.get_current_line_index()

        if line_index == -1:
            return

        if line_index != self.current_line_index:
            self.current_line_index = line_index
            self.line_selected.emit(line_index)

#############################################################################
# Function name:        set_assembly_text                                   #
# Description:          Loads and formats assembly text for display         #
# Parameters:    list – asm_lines: list of assembly lines to display        #
# Return Value: None                                                        #
#############################################################################
    def set_assembly_text(self, asm_lines: list[str]):
        formatted_lines = []
        self.display_to_real_index = []
        self.real_to_display_index = {}

        for real_index, line in enumerate(asm_lines):
            if line.endswith(":") and real_index != 0:
                formatted_lines.append("")
                self.display_to_real_index.append(None)

            display_index = len(formatted_lines)
            formatted_line = f"{real_index}: {line}"
            formatted_lines.append(formatted_line)
            self.display_to_real_index.append(real_index)
            self.real_to_display_index[real_index] = display_index

        self.asm_output.setPlainText("\n".join(formatted_lines))
        self.current_line_index = -1
        self.clear_highlight()

#############################################################################
# Function name:        highlight_line                                      #
# Description:          Highlights a specific assembly line in the panel    #
# Parameters:    int –  index: real assembly line index to highlight        #
# Return Value: None                                                        #
#############################################################################
    def highlight_line(self, index: int):
        if index not in self.real_to_display_index:
            self.clear_highlight()
            return

        self.current_line_index = index
        display_index = self.real_to_display_index[index]

        self.asm_output.blockSignals(True)

        cursor = self.asm_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.movePosition(
            cursor.MoveOperation.Down,
            cursor.MoveMode.MoveAnchor,
            display_index
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

#############################################################################
# Function name:        clear_highlight                                     #
# Description:          Clears the current assembly line highlight          #
# Parameters:    None                                                       #
# Return Value: None                                                        #
#############################################################################
    def clear_highlight(self):
        self.current_line_index = -1
        self.asm_output.blockSignals(True)
        cursor = self.asm_output.textCursor()
        cursor.clearSelection()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.asm_output.setTextCursor(cursor)
        self.asm_output.setExtraSelections([])
        self.asm_output.blockSignals(False)

#############################################################################
# Function name:        get_current_line_index                              #
# Description:          Retrieves the currently selected real line index    #
# Parameters:    None                                                       #
# Return Value: int – selected real assembly line index                     #
#############################################################################
    def get_current_line_index(self) -> int:
        display_index = self.asm_output.textCursor().blockNumber()

        if display_index < 0 or display_index >= len(self.display_to_real_index):
            return -1

        real_index = self.display_to_real_index[display_index]
        return real_index if real_index is not None else -1

#############################################################################
# Function name:        connect_prev_clicked                                #
# Description:          Connects callback to the previous-step button       #
# Parameters:    function – callback: function to call on button click      #
# Return Value: None                                                        #
#############################################################################
    def connect_prev_clicked(self, callback):
        self.prev_button.clicked.connect(callback)

#############################################################################
# Function name:        connect_next_clicked                                #
# Description:          Connects callback to the next-step button           #
# Parameters:    function – callback: function to call on button click      #
# Return Value: None                                                        #
#############################################################################
    def connect_next_clicked(self, callback):
        self.next_button.clicked.connect(callback)