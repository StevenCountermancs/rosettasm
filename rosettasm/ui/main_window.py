import os
import sys
import webbrowser
from types import SimpleNamespace

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QVBoxLayout,
    QFileDialog,
    QDialog,
    QLabel,
    QPushButton,
)
from PyQt6.QtGui import QAction, QGuiApplication
from PyQt6.QtCore import Qt

from ..compiler.compile_driver import compile_source_text
from .source_panel import SourcePanel
from .asm_output_panel import AsmOutputPanel
from .registers_panel import RegistersPanel
from .stack_panel import StackPanel
from .terminal_panel import TerminalPanel


class MainWindow(QMainWindow):
    #############################################################################
    # Function name:        __init__                                            #
    # Description:          Initializes the main RosettASM application window   #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RosettASM")
        screen = QGuiApplication.primaryScreen().availableGeometry()
        w = int(screen.width() * 0.95)
        h = int(screen.height() * 0.9)

        self.resize(w, h)
        self.move(
            screen.x() + (screen.width() - w) // 2,
            screen.y() + (screen.height() - h) // 2,
        )

        self.current_file_path = None
        self.current_asm_index = -1
        self.current_execution_step = -1

        self.asm_lines = []
        self.visible_asm_lines = []
        self.visible_snapshot_indices = []

        self.snapshots = []
        self.execution_snapshots = []
        self.execution_indices = []
        self.tac_to_asm_map = {}
        self.homes = {}

        self.asm_view_mode = "execution"

        self._build_ui()
        self._create_menu_bar()
        self._style_menu_bar()
        self.update_window_title()

    #############################################################################
    # Function name:        _build_ui                                           #
    # Description:          Builds the widgets and layout for the main window   #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def _build_ui(self):
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            background-color: #1e1e1e;
            color: #d4d4d4;
        """)
        self.setCentralWidget(central_widget)

        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        central_widget.setLayout(outer_layout)

        menu_separator = QFrame()
        menu_separator.setFrameShape(QFrame.Shape.NoFrame)
        menu_separator.setFixedHeight(2)
        menu_separator.setStyleSheet("background-color: #3a3a3a")
        outer_layout.addWidget(menu_separator)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(9, 9, 9, 9)
        outer_layout.addLayout(main_layout)

        left_container = QWidget()
        left_grid = QGridLayout()
        left_container.setLayout(left_grid)

        self.source_panel = SourcePanel("Source Code")
        self.source_panel.run_button.clicked.connect(self.run_code)
        self.source_panel.editor.cursorPositionChanged.connect(self.on_source_cursor_changed)

        self.terminal_panel = TerminalPanel("Terminal")

        self.asm_panel = AsmOutputPanel("Assembly Output")
        self.asm_panel.connect_prev_clicked(self.prev_instruction)
        self.asm_panel.connect_next_clicked(self.next_instruction)
        self.asm_panel.line_selected.connect(self.set_current_asm_index)
        self.asm_panel.step_prev_requested.connect(self.on_step_prev_requested)
        self.asm_panel.step_next_requested.connect(self.on_step_next_requested)

        self.registers_panel = RegistersPanel("Registers")
        self.stack_panel = StackPanel("Program Stack")

        left_grid.addWidget(self.source_panel, 0, 0)
        left_grid.addWidget(self.asm_panel, 0, 1)
        left_grid.addWidget(self.terminal_panel, 1, 0)
        left_grid.addWidget(self.registers_panel, 1, 1)

        left_grid.setRowStretch(0, 1)
        left_grid.setRowStretch(1, 1)
        left_grid.setColumnStretch(0, 1)
        left_grid.setColumnStretch(1, 1)

        main_layout.addWidget(left_container, 3)
        main_layout.addWidget(self.stack_panel, 1)

    #############################################################################
    # Function name:        _create_menu_bar                                    #
    # Description:          Creates the menu bar and connects menu actions      #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        view_menu = menu_bar.addMenu("&View")
        run_menu = menu_bar.addMenu("&Run")
        help_menu = menu_bar.addMenu("&Help")

        new_action = QAction("New", self)
        open_action = QAction("Open", self)
        save_action = QAction("Save", self)
        save_as_action = QAction("Save As", self)
        exit_action = QAction("Exit", self)

        view_all_action = QAction("All Assembly", self)
        view_grouped_action = QAction("Grouped by Block", self)
        view_execution_action = QAction("Execution Mode", self)

        run_action = QAction("Run", self)

        legend_action = QAction("Legend", self)
        language_spec_action = QAction("Language Spec", self)
        how_to_use_action = QAction("How to Use", self)

        new_action.triggered.connect(self.new_file)
        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_file)
        save_as_action.triggered.connect(self.save_file_as)
        exit_action.triggered.connect(self.close)

        view_all_action.triggered.connect(self.set_view_all)
        view_grouped_action.triggered.connect(self.set_view_grouped)
        view_execution_action.triggered.connect(self.set_view_execution)

        run_action.triggered.connect(self.run_code)

        legend_action.triggered.connect(self.show_legend)
        language_spec_action.triggered.connect(self.show_language_spec)
        how_to_use_action.triggered.connect(self.show_how_to_use)

        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        view_menu.addAction(view_execution_action)
        view_menu.addAction(view_all_action)
        view_menu.addAction(view_grouped_action)

        run_menu.addAction(run_action)

        help_menu.addAction(legend_action)
        help_menu.addAction(language_spec_action)
        help_menu.addAction(how_to_use_action)

    #############################################################################
    # Function name:        _style_menu_bar                                     #
    # Description:          Applies custom styling to the menu bar              #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def _style_menu_bar(self):
        self.menuBar().setStyleSheet("""
            QMenuBar {
                background-color: #2b2b2b;
                color: white;
            }

            QMenuBar::item {
                background: transparent;
                padding: 4px 10px;
            }

            QMenuBar::item:selected {
                background: #3c3f41;
            }
        """)

    #############################################################################
    # Function name:        run_code                                            #
    # Description:          Compiles source code and updates all UI panels      #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def run_code(self):
        source = self.source_panel.get_source_code()
        self.terminal_panel.clear_output()

        try:
            asm, homes, snapshots, execution_indices, execution_snapshots, tac_to_asm_map = compile_source_text(source)

            self.asm_lines = asm
            self.snapshots = snapshots
            self.execution_snapshots = execution_snapshots
            self.execution_indices = execution_indices
            self.tac_to_asm_map = tac_to_asm_map
            self.homes = homes

            self.current_asm_index = -1
            self.current_execution_step = -1

            self.refresh_asm_view()

            if self.execution_indices:
                self.set_current_execution_step(0)

            self.asm_panel.asm_output.setFocus()

        except Exception as e:
            self.terminal_panel.show_error(str(e))

    #############################################################################
    # Function name:        set_view_all                                        #
    # Description:          Switches assembly panel to full assembly view       #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def set_view_all(self):
        self.asm_view_mode = "all"
        self.refresh_asm_view()
        self.registers_panel.clear_registers()
        self.registers_panel.clear_register_highlights()
        self.stack_panel.reset_stack_display()

    #############################################################################
    # Function name:        set_view_grouped                                    #
    # Description:          Switches assembly panel to grouped source view      #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def set_view_grouped(self):
        self.asm_view_mode = "grouped"
        self.refresh_asm_view()
        self.registers_panel.clear_registers()
        self.registers_panel.clear_register_highlights()
        self.stack_panel.reset_stack_display()

    #############################################################################
    # Function name:        set_view_execution                                  #
    # Description:          Switches assembly panel to execution-step view      #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def set_view_execution(self):
        self.asm_view_mode = "execution"
        self.refresh_asm_view()

        if self.execution_indices:
            step = self.current_execution_step if self.current_execution_step >= 0 else 0
            self.set_current_execution_step(step)

    #############################################################################
    # Function name:        on_source_cursor_changed                            #
    # Description:          Refreshes grouped assembly view on source movement  #
    # Parameters:    int –  line: current source line                           #
    #                int –  index: current column index                         #
    # Return Value: None                                                        #
    #############################################################################
    def on_source_cursor_changed(self, line, index):
        if self.asm_view_mode == "grouped":
            self.refresh_asm_view()

    #############################################################################
    # Function name:        refresh_asm_view                                    #
    # Description:          Rebuilds visible assembly lines for current mode    #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def refresh_asm_view(self):
        if self.asm_view_mode == "grouped":
            source_line = self.get_current_source_line()
            self.visible_snapshot_indices = self.get_asm_indices_for_source_line(source_line)
            self.visible_asm_lines = [self.asm_lines[i] for i in self.visible_snapshot_indices]

            group_source_lines = self.get_source_lines_for_vis_group()
            self.source_panel.highlight_source_lines(group_source_lines)

        else:
            self.source_panel.clear_source_highlight()
            self.visible_snapshot_indices = list(range(len(self.asm_lines)))
            self.visible_asm_lines = list(self.asm_lines)

        self.asm_panel.set_assembly_text(self.visible_asm_lines)

        if self.visible_asm_lines:
            self.current_asm_index = 0
            self.highlight_current_asm_line()

            if self.asm_view_mode == "execution":
                self.update_registers_panel()
                self.update_stack_panel()
        else:
            self.current_asm_index = -1
            self.asm_panel.clear_highlight()

    #############################################################################
    # Function name:        set_current_asm_index                               #
    # Description:          Sets the currently selected visible assembly line   #
    # Parameters:    int –  index: visible assembly line index                  #
    # Return Value: None                                                        #
    #############################################################################
    def set_current_asm_index(self, index: int):
        if not self.visible_asm_lines:
            return

        index = max(0, min(index, len(self.visible_asm_lines) - 1))

        if self.asm_view_mode == "execution":
            actual_index = self.visible_snapshot_indices[index]
            step = self.get_execution_step_for_actual_asm_index(actual_index)

            if step < 0:
                return

            self.set_current_execution_step(step)
            return

        self.current_asm_index = index
        self.highlight_current_asm_line()

    #############################################################################
    # Function name:        set_current_execution_step                          #
    # Description:          Sets the current execution step in execution mode   #
    # Parameters:    int –  step: execution step index                          #
    # Return Value: None                                                        #
    #############################################################################
    def set_current_execution_step(self, step: int):
        if not self.execution_indices:
            return

        step = max(0, min(step, len(self.execution_indices) - 1))

        self.current_execution_step = step
        actual_index = self.execution_indices[step]
        visible_index = self.get_visible_index_for_actual_asm_index(actual_index)

        if visible_index < 0:
            return

        self.current_asm_index = visible_index
        self.highlight_current_asm_line()
        self.update_registers_panel()
        self.update_stack_panel()

    #############################################################################
    # Function name:        highlight_current_asm_line                          #
    # Description:          Highlights the currently selected assembly line     #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def highlight_current_asm_line(self):
        if self.current_asm_index < 0 or self.current_asm_index >= len(self.visible_asm_lines):
            self.asm_panel.clear_highlight()
            return

        self.asm_panel.highlight_line(self.current_asm_index)

    #############################################################################
    # Function name:        on_step_prev_requested                              #
    # Description:          Handles previous-step requests from assembly panel  #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def on_step_prev_requested(self):
        if self.asm_view_mode == "execution":
            self.prev_instruction()
        else:
            self.set_current_asm_index(self.current_asm_index - 1)

    #############################################################################
    # Function name:        on_step_next_requested                              #
    # Description:          Handles next-step requests from assembly panel      #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def on_step_next_requested(self):
        if self.asm_view_mode == "execution":
            self.next_instruction()
        else:
            self.set_current_asm_index(self.current_asm_index + 1)

    #############################################################################
    # Function name:        next_instruction                                    #
    # Description:          Advances to the next execution step                 #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def next_instruction(self):
        self.set_current_execution_step(self.current_execution_step + 1)

    #############################################################################
    # Function name:        prev_instruction                                    #
    # Description:          Moves to the previous execution step                #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def prev_instruction(self):
        self.set_current_execution_step(self.current_execution_step - 1)

    #############################################################################
    # Function name:        get_current_snapshot                                #
    # Description:          Retrieves the snapshot for the current selection    #
    # Parameters:    None                                                       #
    # Return Value: object – current execution or compile-time snapshot         #
    #############################################################################
    def get_current_snapshot(self):
        if self.asm_view_mode == "execution":
            if not self.execution_snapshots:
                return None

            if self.current_execution_step < 0 or self.current_execution_step >= len(self.execution_snapshots):
                return None

            runtime_snapshot = self.execution_snapshots[self.current_execution_step]
            actual_index = self.execution_indices[self.current_execution_step]

            holder_snapshot = None
            if 0 <= actual_index < len(self.snapshots):
                holder_snapshot = self.snapshots[actual_index]

            return SimpleNamespace(
                registers=holder_snapshot.registers if holder_snapshot else runtime_snapshot.registers,
                register_values=runtime_snapshot.register_values,
                memory_values=runtime_snapshot.memory_values,
                highlighted_registers=runtime_snapshot.highlighted_registers,
                highlighted_stack=runtime_snapshot.highlighted_stack,
                source_span=holder_snapshot.source_span if holder_snapshot else None,
            )

        if not self.snapshots:
            return None

        if self.current_asm_index < 0 or self.current_asm_index >= len(self.visible_snapshot_indices):
            return None

        actual_index = self.visible_snapshot_indices[self.current_asm_index]
        return self.snapshots[actual_index]

    #############################################################################
    # Function name:        update_registers_panel                              #
    # Description:          Updates register panel from current snapshot        #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def update_registers_panel(self):
        snapshot = self.get_current_snapshot()
        if snapshot is None:
            return

        self.registers_panel.update_registers(snapshot)

    #############################################################################
    # Function name:        update_stack_panel                                  #
    # Description:          Updates stack panel from current snapshot           #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def update_stack_panel(self):
        snapshot = self.get_current_snapshot()
        if snapshot is None:
            return

        self.stack_panel.update_from_snapshot(snapshot, self.homes)

    #############################################################################
    # Function name:        get_current_source_line                             #
    # Description:          Retrieves the currently selected source line        #
    # Parameters:    None                                                       #
    # Return Value: int – current source line number                            #
    #############################################################################
    def get_current_source_line(self):
        line, index = self.source_panel.editor.getCursorPosition()
        return line + 1

    #############################################################################
    # Function name:        get_snapshot_indices_for_source_line                #
    # Description:          Finds snapshot indices for a given source line      #
    # Parameters:    int –  source_line: source line number                     #
    # Return Value: list – snapshot indices associated with the source line     #
    #############################################################################
    def get_snapshot_indices_for_source_line(self, source_line: int):
        indices = []

        for i, snapshot in enumerate(self.snapshots):
            if snapshot.source_span and snapshot.source_span.line == source_line:
                indices.append(i)

        return indices

    #############################################################################
    # Function name:        get_visible_index_for_actual_asm_index              #
    # Description:          Maps real assembly index to visible assembly index  #
    # Parameters:    int –  actual_index: real assembly line index              #
    # Return Value: int – visible assembly index or -1 if not found             #
    #############################################################################
    def get_visible_index_for_actual_asm_index(self, actual_index: int):
        try:
            return self.visible_snapshot_indices.index(actual_index)
        except ValueError:
            return -1

    #############################################################################
    # Function name:        get_execution_step_for_actual_asm_index             #
    # Description:          Maps real assembly index to execution step index    #
    # Parameters:    int –  actual_index: real assembly line index              #
    # Return Value: int – execution step index or -1 if not found               #
    #############################################################################
    def get_execution_step_for_actual_asm_index(self, actual_index: int):
        try:
            return self.execution_indices.index(actual_index)
        except ValueError:
            return -1

    #############################################################################
    # Function name:        get_asm_indices_for_source_line                     #
    # Description:          Retrieves assembly indices tied to a source line    #
    # Parameters:    int –  source_line: source line number                     #
    # Return Value: list – assembly indices associated with the source line     #
    #############################################################################
    def get_asm_indices_for_source_line(self, source_line: int):
        tac_indices = []

        for tac_index, asm_indices in self.tac_to_asm_map.items():
            if not asm_indices:
                continue

            first_asm_index = asm_indices[0]
            if first_asm_index < 0 or first_asm_index >= len(self.snapshots):
                continue

            snapshot = self.snapshots[first_asm_index]
            if snapshot.source_span and snapshot.source_span.line == source_line:
                tac_indices.append(tac_index)

        tac_indices.sort()

        asm_result = []
        seen = set()

        for tac_index in tac_indices:
            for asm_index in self.tac_to_asm_map.get(tac_index, []):
                if asm_index not in seen:
                    asm_result.append(asm_index)
                    seen.add(asm_index)

        return asm_result

    #############################################################################
    # Function name:        get_source_lines_for_vis_group                      #
    # Description:          Retrieves source lines for current grouped display  #
    # Parameters:    None                                                       #
    # Return Value: list – sorted source line indices for highlighting          #
    #############################################################################
    def get_source_lines_for_vis_group(self):
        source_lines = set()

        for asm_index in self.visible_snapshot_indices:
            if 0 <= asm_index < len(self.snapshots):
                snapshot = self.snapshots[asm_index]
                if snapshot.source_span:
                    source_lines.add(snapshot.source_span.line - 1)

        return sorted(source_lines)

    #############################################################################
    # Function name:        new_file                                            #
    # Description:          Clears the editor and resets all execution state    #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def new_file(self):
        self.source_panel.set_source_code("")
        self.asm_panel.set_assembly_text([])

        self.asm_lines = []
        self.visible_asm_lines = []
        self.visible_snapshot_indices = []
        self.snapshots = []
        self.execution_snapshots = []
        self.execution_indices = []
        self.tac_to_asm_map = {}
        self.homes = {}

        self.current_asm_index = -1
        self.current_execution_step = -1
        self.current_file_path = None

        self.stack_panel.reset_stack_display()
        self.registers_panel.clear_registers()
        self.registers_panel.clear_register_highlights()
        self.update_window_title()

    #############################################################################
    # Function name:        save_file                                           #
    # Description:          Saves source code to the current file path          #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def save_file(self):
        if self.current_file_path is None:
            self.save_file_as()
            return

        try:
            with open(self.current_file_path, "w", encoding="utf-8", newline="") as file:
                file.write(self.source_panel.get_source_code())

            self.update_window_title()

        except Exception as e:
            print(f"Error saving file: {e}")

    #############################################################################
    # Function name:        save_file_as                                        #
    # Description:          Prompts user for file path and saves source code    #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save RosettASM File As",
            "",
            "RosettASM Files (*.rasm);;All Files (*)"
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".rasm"):
            file_path += ".rasm"

        try:
            with open(file_path, "w", encoding="utf-8", newline="") as file:
                file.write(self.source_panel.get_source_code())

            self.current_file_path = file_path
            self.update_window_title()

        except Exception as e:
            print(f"Error saving file: {e}")

    #############################################################################
    # Function name:        open_file                                           #
    # Description:          Opens a source file and resets compiled output      #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open RosettASM File",
            "",
            "RosettASM Files (*.rasm);;All Files (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                source_text = file.read()

            source_text = source_text.replace("\r\n", "\n")

            self.source_panel.set_source_code(source_text)
            self.asm_panel.set_assembly_text([])

            self.asm_lines = []
            self.visible_asm_lines = []
            self.visible_snapshot_indices = []
            self.snapshots = []
            self.execution_snapshots = []
            self.execution_indices = []
            self.tac_to_asm_map = {}
            self.homes = {}

            self.current_asm_index = -1
            self.current_execution_step = -1

            self.stack_panel.reset_stack_display()
            self.registers_panel.clear_registers()
            self.registers_panel.clear_register_highlights()

            self.current_file_path = file_path
            self.update_window_title()

        except Exception as e:
            print(f"Error opening file: {e}")

    #############################################################################
    # Function name:        update_window_title                                 #
    # Description:          Updates window title with current file name         #
    # Parameters:    None                                                       #
    # Return Value: None                                                        #
    #############################################################################
    def update_window_title(self):
        if self.current_file_path:
            filename = os.path.basename(self.current_file_path)
        else:
            filename = "Untitled"

        self.setWindowTitle(f"RosettASM - {filename}")

    def show_legend(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Highlight Legend")
        dialog.setFixedWidth(420)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        dialog.setLayout(layout)

        title = QLabel("Execution Highlight Legend")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: white;
        """)
        layout.addWidget(title)

        legend_items = [
            ("#0A64F0", "Current Instruction", "Indicates the assembly instruction currently being executed."),
            ("#7a4a1e", "Spill", "A register value is saved to memory to free the register."),
            ("#a88f00", "Store", "A value is being written from a register back to memory."),
            ("#2f5d34", "Load", "A value is being loaded from memory into a register."),
            ("#4b3566", "Operation", "An arithmetic or computational operation is being performed."),
        ]

        for color, label_text, description in legend_items:
            layout.addLayout(self._create_legend_row(color, label_text, description))

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

        dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #3c3f41;
                color: white;
                border: 1px solid #555555;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #4a4d50;
            }
        """)

        dialog.exec()


    def _create_legend_row(self, color: str, label_text: str, description: str):
        row = QHBoxLayout()
        row.setSpacing(10)

        swatch = QFrame()
        swatch.setFixedSize(18, 18)
        swatch.setStyleSheet(f"""
            background-color: {color};
            border: 1px solid #cccccc;
        """)

        text_container = QVBoxLayout()
        text_container.setSpacing(2)

        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; color: white;")

        desc = QLabel(description)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: white;")

        text_container.addWidget(label)
        text_container.addWidget(desc)

        row.addWidget(swatch, alignment=Qt.AlignmentFlag.AlignTop)
        row.addLayout(text_container)

        return row

    def show_language_spec(self):
        webbrowser.open("https://github.com/StevenCountermancs/rosettasm/blob/main/rosettasm/docs/language_spec_v1.md", new=2)

    def show_how_to_use(self):
        webbrowser.open("https://github.com/StevenCountermancs/rosettasm/blob/main/rosettasm/docs/how_to_use.md", new=2)