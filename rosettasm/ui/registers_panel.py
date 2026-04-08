from .register_widget import RegisterWidget
from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ..compiler.tac_gen import Temp, Const, Var


class RegistersPanel(QFrame):
    #############################################################################
    # Function name:        __init__                                            #
    # Description:          Initializes the registers panel                     #
    # Parameters:    str –  title: title displayed at the top of the panel      #
    # Return Value: None                                                        #
    #############################################################################
    def __init__(self, title: str = "Registers"):
        super().__init__()

        self.register_widgets = {}

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

        title_label = QLabel(title)
        title_label.setFont(QFont("DM Serif Display", 12))
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        grid_container = QWidget()
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)
        grid_container.setLayout(grid)

        positions = {
            "EAX": (0, 0),
            "EBX": (0, 1),
            "ECX": (0, 2),
            "EDX": (0, 3),
            "ESI": (1, 0),
            "EDI": (1, 1),
            "ESP": (1, 2),
            "EBP": (1, 3),
            "EIP": (2, 1),
            "EFLAGS": (2, 2),
        }

        for reg_name, (row, col) in positions.items():
            widget = RegisterWidget(reg_name)
            self.register_widgets[reg_name] = widget
            grid.addWidget(widget, row, col)

        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)

        main_layout.addWidget(title_label)
        main_layout.addWidget(grid_container)

        self.setLayout(main_layout)

    #############################################################################
    # Function name:        set_register                                        #
    # Description:          Updates a single register widget                    #
    # Parameters:    str –  name: register name                                 #
    #                str –  value: register value                               #
    #                str –  var: associated variable or held value name         #
    # Return Value: None                                                        #
    #############################################################################
    def set_register(self, name: str, value: str, var: str = ""):
        if name in self.register_widgets:
            self.register_widgets[name].set_all(value, var)

    #############################################################################
    # Function name:        clear_registers                                     #
    # Description:          Clears all register values and associated labels    #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def clear_registers(self):
        for name in self.register_widgets:
            self.set_register(name, "", "")

    #############################################################################
    # Function name:        _format_display_name                                #
    # Description:          Formats held register content for UI display        #
    # Parameters:    object – held_value: value currently associated with reg   #
    #                str –  reg_name: register name being formatted             #
    # Return Value: str – formatted display label                               #
    #############################################################################
    def _format_display_name(self, held_value, reg_name=None):
        if reg_name == "EBP":
            return "(base pointer)"
        if reg_name == "ESP":
            return "(stack pointer)"
        if reg_name == "EIP":
            return "(instr pointer)"

        if held_value is None:
            return ""

        if isinstance(held_value, str):
            return held_value

        if isinstance(held_value, Temp):
            suffix = held_value.name[1:]
            if suffix.isdigit():
                return f"result {int(suffix) + 1}"
            return "result"

        if isinstance(held_value, Var):
            return held_value.name

        if isinstance(held_value, Const):
            return f""

        return str(held_value)

    #############################################################################
    # Function name:        update_registers                                    #
    # Description:          Updates all register widgets from a snapshot        #
    # Parameters:    object – snapshot: snapshot containing register state      #
    # Return Value: None                                                        #
    #############################################################################
    def update_registers(self, snapshot):
        self.clear_registers()
        self.clear_register_highlights()

        for reg_enum, held_value in snapshot.registers.items():
            reg_name = reg_enum.name
            numeric_value = snapshot.register_values.get(reg_enum)

            display_value = "" if numeric_value is None else str(numeric_value)
            display_name = self._format_display_name(held_value, reg_name)

            self.set_register(reg_name, display_value, display_name)

        for reg_name, color in snapshot.highlighted_registers.items():
            if reg_name in self.register_widgets:
                self.register_widgets[reg_name].set_highlight(color)

    #############################################################################
    # Function name:        clear_register_highlights                           #
    # Description:          Clears highlighting from all register widgets       #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def clear_register_highlights(self):
        for widget in self.register_widgets.values():
            widget.clear_highlight()