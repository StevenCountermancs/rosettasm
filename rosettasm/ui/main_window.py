import os
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QFileDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction, QGuiApplication
from ..compiler.compile_driver import compile_source_text
from .source_panel import SourcePanel
from .asm_output_panel import AsmOutputPanel
from .registers_panel import RegistersPanel
from .stack_panel import StackPanel
from .terminal_panel import TerminalPanel


class MainWindow(QMainWindow):
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

        self._build_ui()
        self._create_menu_bar()
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

        self.current_file_path = None
        self.update_window_title()
        self.current_asm_index = -1
        self.asm_lines = []
        self.snapshots = []
        self.asm_view_mode = "all"
        self.visible_asm_lines = []
        self.visible_snapshot_indices = []
        self.homes = {}

    def _build_ui(self):
        central_widget = QWidget()
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
        view_grouped_action = QAction("Grouped by Source Line", self)

        run_action = QAction("Run", self)

        new_action.triggered.connect(self.new_file)
        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_file)
        save_as_action.triggered.connect(self.save_file_as)
        exit_action.triggered.connect(self.close)

        view_all_action.triggered.connect(self.set_view_all)
        view_grouped_action.triggered.connect(self.set_view_grouped)

        run_action.triggered.connect(self.run_code)

        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        view_menu.addAction(view_all_action)
        view_menu.addAction(view_grouped_action)

        run_menu.addAction(run_action)

    def _create_terminal_panel(self, title: str):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.Box)

        layout = QVBoxLayout()

        label = QLabel(title)
        label.setFont(QFont("DM Serif Display", 12))

        terminal = QTextEdit()
        terminal.setReadOnly(True)

        layout.addWidget(label)
        layout.addWidget(terminal)

        frame.setLayout(layout)
        return frame

    def run_code(self):
        source = self.source_panel.get_source_code()
        self.terminal_panel.clear_output()

        try:
            asm, homes, snapshots = compile_source_text(source)
            self.asm_lines = asm
            self.snapshots = snapshots
            self.homes = homes

            self.refresh_asm_view()
            self.asm_panel.asm_output.setFocus()

        except Exception as e:
            self.terminal_panel.show_error(str(e))
            return

    def set_view_all(self):
        self.asm_view_mode = "all"
        self.refresh_asm_view()

    def set_view_grouped(self):
        self.asm_view_mode = "grouped"
        self.refresh_asm_view()

    def on_source_cursor_changed(self, line, index):
        if self.asm_view_mode == "grouped":
            self.refresh_asm_view()

    def get_current_source_line(self):
        line, index = self.source_panel.editor.getCursorPosition()
        return line + 1

    def get_snapshot_indices_for_source_line(self, source_line: int):
        indices = []

        for i, snapshot in enumerate(self.snapshots):
            if snapshot.source_span and snapshot.source_span.line == source_line:
                indices.append(i)

        return indices

    def refresh_asm_view(self):
        if self.asm_view_mode == "grouped":
            source_line = self.get_current_source_line()
            self.source_panel.highlight_source_line(source_line - 1)
            self.visible_snapshot_indices = self.get_snapshot_indices_for_source_line(source_line)
            self.visible_asm_lines = [self.asm_lines[i] for i in self.visible_snapshot_indices]
        else:
            self.source_panel.clear_source_highlight()
            self.visible_snapshot_indices = list(range(len(self.asm_lines)))
            self.visible_asm_lines = list(self.asm_lines)

        self.asm_panel.set_assembly_text(self.visible_asm_lines)

        if self.visible_asm_lines:
            self.current_asm_index = 0
            self.highlight_current_asm_line()
            self.update_registers_panel()
            self.update_stack_panel()
        else:
            self.current_asm_index = -1
            self.asm_panel.clear_highlight()

    def set_current_asm_index(self, index: int):
        if not self.visible_asm_lines:
            return

        index = max(0, min(index, len(self.visible_asm_lines) - 1))
        self.current_asm_index = index
        self.highlight_current_asm_line()
        self.update_registers_panel()
        self.update_stack_panel()

    def highlight_current_asm_line(self):
        if self.current_asm_index < 0 or self.current_asm_index >= len(self.visible_asm_lines):
            self.asm_panel.clear_highlight()
            return

        self.asm_panel.highlight_line(self.current_asm_index)

    def get_current_snapshot(self):
        if not self.snapshots:
            return None

        if self.current_asm_index < 0 or self.current_asm_index >= len(self.visible_snapshot_indices):
            return None

        actual_index = self.visible_snapshot_indices[self.current_asm_index]
        return self.snapshots[actual_index]

    def update_registers_panel(self):
        snapshot = self.get_current_snapshot()
        if snapshot is None:
            return

        self.registers_panel.update_registers(snapshot)

    def update_stack_panel(self):
        snapshot = self.get_current_snapshot()
        if snapshot is None:
            return

        self.stack_panel.update_from_snapshot(snapshot, self.homes)

    def next_instruction(self):
        self.set_current_asm_index(self.current_asm_index + 1)

    def prev_instruction(self):
        self.set_current_asm_index(self.current_asm_index - 1)

    def new_file(self):
        self.source_panel.set_source_code("")
        self.asm_panel.set_assembly_text([])
        self.asm_lines = []
        self.visible_asm_lines = []
        self.visible_snapshot_indices = []
        self.snapshots = []
        self.homes = {}
        self.current_asm_index = -1
        self.current_file_path = None
        self.stack_panel.reset_stack_display()
        self.update_window_title()

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
            self.homes = {}
            self.current_asm_index = -1
            self.stack_panel.reset_stack_display()

            self.current_file_path = file_path
            self.update_window_title()

        except Exception as e:
            print(f"Error opening file: {e}")

    def update_window_title(self):
        if self.current_file_path:
            filename = os.path.basename(self.current_file_path)
        else:
            filename = "Untitled"

        self.setWindowTitle(f"RosettASM - {filename}")