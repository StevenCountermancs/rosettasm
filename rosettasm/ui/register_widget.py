from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontMetrics

class RegisterWidget(QFrame):
    #############################################################################
    # Function name:        __init__                                            #
    # Description:          Initializes a register display widget               #
    # Parameters:    str –  name: register name                                 #
    #                str –  value: initial register value                       #
    #                str –  var: variable currently associated with register    #
    # Return Value: None                                                        #
    #############################################################################
    def __init__(self, name: str, value: str = "", var: str = ""):
        super().__init__()

        self.name = name
        self.setObjectName("registerWidget")
        self.full_value_text = "" if value is None else str(value)
        self.full_var_text = var if var else "--"

        self.base_style = """
            #registerWidget {
                border: 1px solid #666;
                border-radius: 8px;
                background-color: #2b2b2b;
            }
            QLabel {
                background: transparent;
                border: none;
                color: #d4d4d4;
            }
        """
        self._build_ui(name)
        self.setStyleSheet(self.base_style)
        self._refresh_text()

    #############################################################################
    # Function name:        _build_ui                                           #
    # Description:          Builds the labels and layout for the register widget#
    # Parameters:    str –  name: register name                                 #
    # Return Value: None                                                        #
    #############################################################################
    def _build_ui(self, name: str):
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)
        
        self.name_label = QLabel(name)
        self.name_label.setFont(QFont("DM Serif Display", 11))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.value_label = QLabel("")
        self.value_label.setFont(QFont("Consolas", 11))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.var_label = QLabel("")
        self.var_label.setFont(QFont("Consolas", 9))
        self.var_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.name_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.value_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.var_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        layout.addWidget(self.name_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.var_label)

        self.setLayout(layout)
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    #############################################################################
    # Function name:        _elide_for_label                                    #
    # Description:          Shortens text to fit within a label width           #
    # Parameters:    str –  text: text to shorten                               #
    #                QLabel – label: label used for width measurement           #
    # Return Value: str – elided text for display                               #
    #############################################################################
    def _elide_for_label(self, text: str, label: QLabel) -> str:
        if not text:
            return ""
        
        metrics = QFontMetrics(label.font())
        available_width = max(0, label.width() - 4)
        return metrics.elidedText(
            text,
            Qt.TextElideMode.ElideRight,
            available_width,
        )
    
    #############################################################################
    # Function name:        _refresh_text                                       #
    # Description:          Updates displayed value and variable text           #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def _refresh_text(self):
        value_display = self._elide_for_label(self.full_value_text, self.value_label)
        var_display = self._elide_for_label(self.full_var_text, self.var_label)

        self.value_label.setText(value_display)
        self.var_label.setText(var_display)

        self.value_label.setToolTip(self.full_value_text if self.full_value_text else "")
        self.var_label.setToolTip(self.full_var_text if self.full_var_text and self.full_var_text != "--" else "")

    #############################################################################
    # Function name:        resizeEvent                                         #
    # Description:          Refreshes displayed text when widget is resized     #
    # Parameters:    QResizeEvent – event: resize event for the widget          #
    # Return Value: None                                                        #
    #############################################################################
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_text()

    #############################################################################
    # Function name:        set_value                                           #
    # Description:          Updates the displayed register value                #
    # Parameters:    str –  value: new register value                           #
    # Return Value: None                                                        #
    #############################################################################
    def set_value(self, value: str):
        self.full_value_text = "" if value is None else str(value)
        self._refresh_text()

    #############################################################################
    # Function name:        set_var                                             #
    # Description:          Updates the displayed associated variable           #
    # Parameters:    str –  var: new associated variable name                   #
    # Return Value: None                                                        #
    #############################################################################
    def set_var(self, var: str):
        self.full_var_text = var if var else "--"
        self._refresh_text()

    #############################################################################
    # Function name:        set_all                                             #
    # Description:          Updates both register value and associated variable #
    # Parameters:    str –  value: new register value                           #
    #                str –  var: new associated variable name                   #
    # Return Value: None                                                        #
    #############################################################################
    def set_all(self, value: str, var: str):
        self.full_value_text = "" if value is None else str(value)
        self.full_var_text = var if var else "--"
        self._refresh_text()

    #############################################################################
    # Function name:        set_highlight                                       #
    # Description:          Applies a highlight color to the register widget    #
    # Parameters:    str –  color: highlight color name                         #
    # Return Value: None                                                        #
    #############################################################################
    def set_highlight(self, color: str):
        color_map = {
            "green": "#2f5d34",
            "yellow": "#a88f00",
            "purple": "#4b3566",
            "orange": "#7a4a1e",
        }

        bg = color_map.get(color, "#2b2b2b")

        self.setStyleSheet(f"""
            #registerWidget {{
                border: 1px solid #666;
                border-radius: 8px;
                background-color: {bg};
            }}
            QLabel {{
                background: transparent;
                border: none;
                color: #d4d4d4
            }}
        """)

    #############################################################################
    # Function name:        clear_highlight                                     #
    # Description:          Restores the default widget styling                 #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def clear_highlight(self):
        self.setStyleSheet(self.base_style)