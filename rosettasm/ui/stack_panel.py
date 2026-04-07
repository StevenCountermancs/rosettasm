from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QFontMetrics
from ..compiler.tac_gen import Var, Temp


class StackPanel(QFrame):
    def __init__(self, title="Program Stack"):
        super().__init__()

        self.setFrameShape(QFrame.Shape.Box)

        self.title_font = QFont("DM Serif Display", 12)
        self.header_font = QFont("Consolas", 10)
        self.header_font.setBold(True)
        self.cell_font = QFont("Consolas", 10)

        self.outer_layout = QVBoxLayout()
        self.outer_layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.outer_layout)

        self.title_label = QLabel(title)
        self.title_label.setFont(self.title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.outer_layout.addWidget(self.title_label)

        self.stack_widget = QWidget()
        self.stack_layout = QGridLayout()
        self.stack_layout.setContentsMargins(8, 8, 8, 8)
        self.stack_layout.setHorizontalSpacing(16)
        self.stack_layout.setVerticalSpacing(8)
        self.stack_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stack_widget.setLayout(self.stack_layout)

        self.stack_layout.setColumnStretch(0, 1)  # Offset
        self.stack_layout.setColumnStretch(1, 2)  # Name
        self.stack_layout.setColumnStretch(2, 1)  # Value

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(self.stack_widget)

        self.outer_layout.addWidget(self.scroll_area)
        
        self.dynamic_row_widgets = []
        self._build_static_frame()
        self.set_frame_rows_visible(False)
        self.dynamic_rows_by_offset = {}

    def _create_cell(self, text: str, alignment, font=None):
        label = QLabel("")
        label.setFont(font if font else self.cell_font)
        label.setAlignment(alignment)

        label.full_text = text if text else ""

        label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        self._set_elided_text(label)

        return label

    def _create_ebp_separator(self):
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        left_line = QFrame()
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setFrameShadow(QFrame.Shadow.Sunken)

        right_line = QFrame()
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setFrameShadow(QFrame.Shadow.Sunken)

        label = QLabel("EBP")
        label.setFont(self.header_font)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(left_line, 1)
        layout.addWidget(label)
        layout.addWidget(right_line, 1)

        container.setLayout(layout)
        return container

    def _build_static_frame(self):
        row = 0

        self.stack_layout.addWidget(
            self._create_cell("Offset", Qt.AlignmentFlag.AlignLeft, self.header_font), row, 0
        )
        self.stack_layout.addWidget(
            self._create_cell("Name", Qt.AlignmentFlag.AlignCenter, self.header_font), row, 1
        )
        self.stack_layout.addWidget(
            self._create_cell("Value", Qt.AlignmentFlag.AlignRight, self.header_font), row, 2
        )
        row += 1

        self.return_offset_label = self._create_cell("[ebp+4]", Qt.AlignmentFlag.AlignLeft)
        self.return_name_label = self._create_cell("Return Addr", Qt.AlignmentFlag.AlignCenter)
        self.return_value_label = self._create_cell("", Qt.AlignmentFlag.AlignRight)

        self.saved_offset_label = self._create_cell("[ebp+0]", Qt.AlignmentFlag.AlignLeft)
        self.saved_name_label = self._create_cell("Saved EBP", Qt.AlignmentFlag.AlignCenter)
        self.saved_value_label = self._create_cell("", Qt.AlignmentFlag.AlignRight)

        self.stack_layout.addWidget(self.return_offset_label, row, 0)
        self.stack_layout.addWidget(self.return_name_label, row, 1)
        self.stack_layout.addWidget(self.return_value_label, row, 2)
        row += 1

        self.stack_layout.addWidget(self.saved_offset_label, row, 0)
        self.stack_layout.addWidget(self.saved_name_label, row, 1)
        self.stack_layout.addWidget(self.saved_value_label, row, 2)
        row += 1

        self.ebp_separator = self._create_ebp_separator()
        self.stack_layout.addWidget(self.ebp_separator, row, 0, 1, 3)
        row += 1

        self.first_dynamic_row = row

    def set_frame_rows_visible(self, visible: bool):
        widgets = [
            self.return_offset_label,
            self.return_name_label,
            self.return_value_label,
            self.saved_offset_label,
            self.saved_name_label,
            self.saved_value_label,
            self.ebp_separator,
        ]

        for widget in widgets:
            widget.setVisible(visible)

    def clear_dynamic_rows(self):
        for widget in self.dynamic_row_widgets:
            self.stack_layout.removeWidget(widget)
            widget.deleteLater()
        
        self.dynamic_row_widgets.clear()
        self.dynamic_rows_by_offset.clear()

    def add_stack_row(self, offset: str, name: str, value: str, kind: str, symbol=None):
        row = self.first_dynamic_row + len(self.dynamic_rows_by_offset)

        offset_label = self._create_cell(offset, Qt.AlignmentFlag.AlignLeft)
        name_label = self._create_cell(name, Qt.AlignmentFlag.AlignCenter)
        value_label = self._create_cell(value, Qt.AlignmentFlag.AlignRight)

        self.stack_layout.addWidget(offset_label, row, 0)
        self.stack_layout.addWidget(name_label, row, 1)
        self.stack_layout.addWidget(value_label, row, 2)

        self.dynamic_row_widgets.extend([offset_label, name_label, value_label])

        self.dynamic_rows_by_offset[offset] = {
            "offset": offset_label,
            "name": name_label,
            "value": value_label,
            "kind": kind,
            "symbol": symbol,
        }

    def populate_from_homes(self, homes):
        self.clear_dynamic_rows()

        var_entries = []
        temp_entries = []
        for val, home in homes.items():
            if isinstance(val, Var):
                var_entries.append((val, home))
            elif isinstance(val, Temp):
                temp_entries.append((val, home))

        var_entries.sort(
            key=lambda entry: self._extract_offset(entry[1]),
            reverse=True
        )
        
        temp_entries.sort(
            key=lambda entry: self._extract_offset(entry[1]),
            reverse=True
        )

        for var, home in var_entries:
            self.add_stack_row(home, var.name, "", "var", var)

        for temp, home in temp_entries:
            self.add_stack_row(home, "", "", "temp", temp)

        QTimer.singleShot(0, self._refresh_all_dynamic_cells)

    def _extract_offset(self, home: str):
        inside = home.strip()[1:-1]
        if inside.startswith("ebp"):
            offset_part = inside[3:]
            return int(offset_part)
        return 0
    
    def _esp_has_reserved_frame(self, esp_value):
        if not isinstance(esp_value, str):
            return False
        if esp_value == "ebp":
            return False
        if esp_value.startswith("ebp-"):
            suffix = esp_value[4:]
            return suffix.isdigit()
        return False

    def _esp_is_in_active_frame(self, esp_value):
        if not isinstance(esp_value, str):
            return False

        if esp_value == "stack top":
            return False

        if esp_value == "saved ebp slot":
            return True

        if esp_value == "ebp":
            return True

        if esp_value.startswith("ebp-"):
            suffix = esp_value[4:]
            return suffix.isdigit()

        return False
    
    def update_from_snapshot(self, snapshot, homes):
        esp_value = snapshot.register_values.get(next(
            reg for reg in snapshot.register_values.keys() if getattr(reg, "name", "") == "ESP"
        ), None)

        should_show_static_rows = self._esp_is_in_active_frame(esp_value)
        self.set_frame_rows_visible(should_show_static_rows)
        self.clear_stack_highlights()

        self.saved_value_label.full_text = (
            str(snapshot.memory_values.get("[ebp]", ""))
            if should_show_static_rows else ""
        )
        self._set_elided_text(self.saved_value_label)

        self.return_value_label.full_text = (
            str(snapshot.memory_values.get("[ebp+4]", ""))
            if should_show_static_rows else ""
        )
        self._set_elided_text(self.return_value_label)

        should_show_dynamic_rows = self._esp_has_reserved_frame(esp_value)

        if should_show_dynamic_rows:
            if len(self.dynamic_rows_by_offset) != len(homes):
                self.populate_from_homes(homes)
        else:
            if self.dynamic_rows_by_offset:
                self.clear_dynamic_rows()

        for offset, row in self.dynamic_rows_by_offset.items():
            kind = row["kind"]
            symbol = row["symbol"]
            value = snapshot.memory_values.get(offset)

            if kind == "var":
                row["name"].full_text = self._format_display_name(symbol)
                self._set_elided_text(row["name"])

                row["value"].full_text = "" if value is None else str(value)
                self._set_elided_text(row["value"])

            elif kind == "temp":
                if value is None:
                    row["name"].full_text = ""
                    self._set_elided_text(row["name"])

                    row["value"].full_text = ""
                    self._set_elided_text(row["value"])
                else:
                    row["name"].full_text = self._format_display_name(symbol)
                    self._set_elided_text(row["name"])

                    row["value"].full_text = str(value)
                    self._set_elided_text(row["value"])

        if should_show_static_rows and "[ebp]" in snapshot.highlighted_stack:
            style = self._highlight_cell_style(snapshot.highlighted_stack["[ebp]"])
            self.saved_offset_label.setStyleSheet(style)
            self.saved_name_label.setStyleSheet(style)
            self.saved_value_label.setStyleSheet(style)

        if should_show_static_rows and "[ebp+4]" in snapshot.highlighted_stack:
            style = self._highlight_cell_style(snapshot.highlighted_stack["[ebp+4]"])
            self.return_offset_label.setStyleSheet(style)
            self.return_name_label.setStyleSheet(style)
            self.return_value_label.setStyleSheet(style)

        for offset, color in snapshot.highlighted_stack.items():
            if offset in self.dynamic_rows_by_offset:
                row = self.dynamic_rows_by_offset[offset]
                style = self._highlight_cell_style(color)
                row["offset"].setStyleSheet(style)
                row["name"].setStyleSheet(style)
                row["value"].setStyleSheet(style)

    def _format_display_name(self, symbol):
        if isinstance(symbol, Temp):
            suffix = symbol.name[1:]
            if suffix.isdigit():
                return f"result {int(suffix) + 1}"
            return "result"
        return getattr(symbol, "name", str(symbol))
    
    def _set_elided_text(self, label: QLabel):
        text = getattr(label, "full_text", "")
        if not text:
            label.setText("")
            label.setToolTip("")
            return
        
        metrics = QFontMetrics(label.font())
        available_width = max(0, label.width() - 4)

        elided = metrics.elidedText(
            text,
            Qt.TextElideMode.ElideRight,
            available_width
        )

        label.setText(elided)
        label.setToolTip(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        self._set_elided_text(self.return_offset_label)
        self._set_elided_text(self.return_name_label)
        self._set_elided_text(self.return_value_label)
        self._set_elided_text(self.saved_offset_label)
        self._set_elided_text(self.saved_name_label)
        self._set_elided_text(self.saved_value_label)
        
        for row in self.dynamic_rows_by_offset.values():
            self._set_elided_text(row["offset"])
            self._set_elided_text(row["name"])
            self._set_elided_text(row["value"])
        
    def _base_cell_style(self):
        return ""
    
    def _highlight_cell_style(self, color: str):
        color_map = {
            "green": "#2f5d34",
            "yellow": "#a88f00",
            "purple": "#4b3566",
            "orange": "#7a4a1e",
        }
        bg = color_map.get(color, "transparent")
        return f"""
            QLabel {{
                background-color: {bg};
            }}
        """
    
    def clear_stack_highlights(self):
        static_widgets = [
            self.return_offset_label,
            self.return_name_label,
            self.return_value_label,
            self.saved_offset_label,
            self.saved_name_label,
            self.saved_value_label,
        ]

        for widget in static_widgets:
            widget.setStyleSheet(self._base_cell_style())

        for row in self.dynamic_rows_by_offset.values():
            row["offset"].setStyleSheet(self._base_cell_style())
            row["name"].setStyleSheet(self._base_cell_style())
            row["value"].setStyleSheet(self._base_cell_style())

    def _refresh_all_dynamic_cells(self):
        self._set_elided_text(self.return_offset_label)
        self._set_elided_text(self.return_name_label)
        self._set_elided_text(self.return_value_label)
        self._set_elided_text(self.saved_offset_label)
        self._set_elided_text(self.saved_name_label)
        self._set_elided_text(self.saved_value_label)

        for row in self.dynamic_rows_by_offset.values():
            self._set_elided_text(row["offset"])
            self._set_elided_text(row["name"])
            self._set_elided_text(row["value"])

    def reset_stack_display(self):
        self.clear_stack_highlights()
        self.clear_dynamic_rows()
        self.set_frame_rows_visible(False)

        static_labels = [
            self.return_offset_label,
            self.return_name_label,
            self.return_value_label,
            self.saved_offset_label,
            self.saved_name_label,
            self.saved_value_label,
        ]

        for label in static_labels:
            label.setStyleSheet(self._base_cell_style())
        
        self.return_value_label.full_text = ""
        self.saved_value_label.full_text = ""
        
        self._set_elided_text(self.return_value_label)
        self._set_elided_text(self.saved_value_label)
        