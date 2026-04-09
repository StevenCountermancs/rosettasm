from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QTextEdit,
)
from PyQt6.QtGui import QFont


class TerminalPanel(QFrame):
    #############################################################################
    # Function name:        __init__                                            #
    # Description:          Initializes the terminal output panel               #
    # Parameters:    str –  title: title displayed at the top of the panel      #
    # Return Value: None                                                        #
    #############################################################################
    def __init__(self, title: str = "Terminal"):
        super().__init__()

        self.setFrameShape(QFrame.Shape.Box)
        self._build_ui(title)

    #############################################################################
    # Function name:        _build_ui                                           #
    # Description:          Builds the widgets and layout for the panel         #
    # Parameters:    str –  title: title displayed at the top of the panel      #
    # Return Value: None                                                        #
    #############################################################################
    def _build_ui(self, title: str):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setFont(QFont("DM Serif Display", 12))

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 11))
        self.output.setStyleSheet("""
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: none;
        """)

        layout.addWidget(title_label)
        layout.addWidget(self.output)

        self.setLayout(layout)

    #############################################################################
    # Function name:        set_text                                            #
    # Description:          Replaces terminal contents with new text            #
    # Parameters:    str –  text: text to display in the terminal               #
    # Return Value: None                                                        #
    #############################################################################
    def set_text(self, text: str):
        self.output.setPlainText(text)

    #############################################################################
    # Function name:        append_text                                         #
    # Description:          Appends text to the terminal output                 #
    # Parameters:    str –  text: text to append                                #
    # Return Value: None                                                        #
    #############################################################################
    def append_text(self, text: str):
        self.output.append(text)

    #############################################################################
    # Function name:        clear_output                                        #
    # Description:          Clears all text from the terminal                   #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def clear_output(self):
        self.output.clear()

    #############################################################################
    # Function name:        show_error                                          #
    # Description:          Displays an error message in the terminal           #
    # Parameters:    str –  message: error message to display                   #
    # Return Value: None                                                        #
    #############################################################################
    def show_error(self, message: str):
        self.output.setPlainText(f"Error: {message}")