from typing import Dict, Any
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QScrollArea,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QDoubleSpinBox,
    QSpinBox,
    QLineEdit,
    QComboBox,
    QColorDialog,
    QCheckBox,
    QFileDialog,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor

from gui.schedule_widget import ScheduleWidget


class SettingsPanel(QWidget):
    """
    Right-side panel with configuration form and action buttons.
    """

    configChanged = Signal()  # Emitted when any field changes
    scheduleChanged = Signal()  # Re-emitted from schedule widget
    fetchCoversRequested = Signal()  # Re-emitted
    savePresetRequested = Signal()
    loadPresetRequested = Signal()
    exportRequested = Signal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.widgets: Dict[str, Any] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        layout.addWidget(self._create_toolbar())

        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        self.form_layout = QFormLayout(form_widget)
        self.form_layout.setSpacing(12)
        self.form_layout.setContentsMargins(15, 15, 15, 15)

        self._create_form_widgets()

        scroll.setWidget(form_widget)
        layout.addWidget(scroll)

        # Export button
        export_btn = QPushButton("💾 Save to Disk")
        export_btn.setMinimumHeight(50)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a7c59;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a8c69;
            }
        """)
        export_btn.clicked.connect(self.exportRequested.emit)
        layout.addWidget(export_btn)

    def _create_toolbar(self):
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(5, 5, 5, 5)

        open_btn = QPushButton("📂 Open Preset")
        open_btn.clicked.connect(self.loadPresetRequested.emit)

        save_btn = QPushButton("💾 Save Preset")
        save_btn.clicked.connect(self.savePresetRequested.emit)

        layout.addWidget(open_btn)
        layout.addWidget(save_btn)
        return toolbar

    def _create_form_widgets(self):
        # Manga Title
        self._add_string_widget("manga_title", "Manga Title")

        # Schedule Widget (Custom)
        self.schedule_widget = ScheduleWidget()
        self.schedule_widget.scheduleChanged.connect(self.scheduleChanged.emit)
        self.schedule_widget.fetchCoversRequested.connect(
            self.fetchCoversRequested.emit
        )
        self.form_layout.addRow(self.schedule_widget)

        # Image Processing
        self.form_layout.addRow(QLabel("<b>Image Processing</b>"))
        self._add_float_widget("zoom_factor", "Zoom Factor", 0.1, 3.0, 0.1)
        self._add_float_widget("vertical_offset", "Vertical Offset", -1.0, 1.0, 0.01)

        # Layout
        self.form_layout.addRow(QLabel("<b>Layout</b>"))
        self._add_int_widget("cols", "Columns", 1, 10)
        self._add_float_widget("title_row_height", "Title Row Height", 0.5, 10.0, 0.1)
        self._add_float_widget("vertical_padding", "Vertical Padding", 0.0, 5.0, 0.1)
        self._add_float_widget("bottom_margin", "Bottom Margin", 0.0, 5.0, 0.1)
        self._add_float_widget(
            "horizontal_padding", "Horizontal Padding", 0.0, 5.0, 0.1
        )
        self._add_float_widget("column_spacing", "Column Spacing", 0.0, 5.0, 0.1)

        # Shape
        self.form_layout.addRow(QLabel("<b>Frame Shape</b>"))
        self._add_combo_widget(
            "shape_type",
            "Shape Type",
            ["parallelogram", "rhombus", "rectangle", "hexagon"],
            "parallelogram",
        )
        self._add_float_widget("shape_width", "Frame Width", 0.5, 10.0, 0.1)
        self._add_float_widget("shape_height", "Frame Height", 0.5, 10.0, 0.1)
        self._add_float_widget("shape_spacing", "Frame Spacing", 0.0, 5.0, 0.1)
        self._add_color_widget("shape_border_color", "Border Color")
        self._add_float_widget("shape_shadow_alpha", "Shadow Alpha", 0.0, 1.0, 0.05)
        self._add_float_widget("shape_skew_angle", "Skew Angle", -90.0, 90.0, 1.0)
        self._add_float_widget(
            "shape_rotation_angle", "Rotation Angle", -180.0, 180.0, 1.0
        )

        # Stagger
        self.form_layout.addRow(QLabel("<b>Stagger</b>"))
        self._add_combo_widget(
            "stagger_type", "Stagger Type", ["none", "alternating", "wave"], "none"
        )
        self._add_float_widget("stagger_offset", "Stagger Offset", 0.0, 2.0, 0.1)

        # Title
        self.form_layout.addRow(QLabel("<b>Title</b>"))
        self._add_int_widget("title_fontsize", "Title Font Size", 10, 100)
        self._add_combo_widget(
            "title_fontweight", "Title Weight", ["normal", "bold"], "bold"
        )
        self._add_color_widget("title_color", "Title Color")
        self._add_string_widget("title_fontfamily", "Title Font Family")

        # Text
        self.form_layout.addRow(QLabel("<b>Text</b>"))
        self._add_int_widget("date_fontsize", "Date Font Size", 8, 50)
        self._add_int_widget("volume_fontsize", "Volume Font Size", 8, 50)
        self._add_color_widget("text_color", "Text Color")

        # Background
        self.form_layout.addRow(QLabel("<b>Background</b>"))
        self._add_color_widget("background_color", "Background Color")
        self._add_color_widget(
            "frame_border_color", "Frame Border Color"
        )  # Note: legacy naming in config?

        # Lineart
        self.form_layout.addRow(QLabel("<b>Background Line Art</b>"))
        self._add_checkbox_widget("background_lineart_enabled", "Enable Line Art")
        self._add_file_widget("background_lineart_path", "Line Art Path")
        self._add_float_widget(
            "background_lineart_alpha", "Line Art Alpha", 0.0, 1.0, 0.05
        )

        # Output
        self.form_layout.addRow(QLabel("<b>Output</b>"))
        self._add_string_widget("output_dir", "Output Directory")
        self._add_int_widget("dpi", "DPI", 72, 600)

    # --- Widget Helpers ---
    def _add_float_widget(self, name, label, min_val, max_val, step):
        widget = QDoubleSpinBox()
        widget.setRange(min_val, max_val)
        widget.setSingleStep(step)
        widget.setValue(
            getattr(self.config, name, 0)
            if not name.startswith("shape_") and not name.startswith("stagger_")
            else 0
        )
        widget.valueChanged.connect(self.configChanged.emit)
        self.widgets[name] = widget
        self.form_layout.addRow(label, widget)

    def _add_int_widget(self, name, label, min_val, max_val):
        widget = QSpinBox()
        widget.setRange(min_val, max_val)
        widget.setValue(getattr(self.config, name, 0))
        widget.valueChanged.connect(self.configChanged.emit)
        self.widgets[name] = widget
        self.form_layout.addRow(label, widget)

    def _add_string_widget(self, name, label):
        widget = QLineEdit()
        widget.setText(getattr(self.config, name, ""))
        widget.textChanged.connect(self.configChanged.emit)
        self.widgets[name] = widget
        self.form_layout.addRow(label, widget)

    def _add_color_widget(self, name, label):
        widget = QLineEdit()
        val = getattr(self.config, name, "#ffffff")
        if name.startswith("shape_"):
            val = self.config.shape_preset.get(
                name.replace("shape_", ""), "#ffffff"
            )  # Simplified logic for now
        widget.setText(val)
        widget.textChanged.connect(self.configChanged.emit)

        btn = QPushButton("🎨")
        btn.setMaximumWidth(40)
        btn.clicked.connect(lambda: self._pick_color(widget))

        layout = QHBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(btn)

        self.widgets[name] = widget
        self.form_layout.addRow(label, layout)

    def _pick_color(self, line_edit):
        color = QColorDialog.getColor(initial=QColor(line_edit.text()))
        if color.isValid():
            line_edit.setText(color.name())

    def _add_combo_widget(self, name, label, options, default):
        widget = QComboBox()
        widget.addItems(options)
        widget.currentTextChanged.connect(self.configChanged.emit)
        self.widgets[name] = widget
        self.form_layout.addRow(label, widget)

    def _add_checkbox_widget(self, name, label):
        widget = QCheckBox(label)
        widget.setChecked(getattr(self.config, name, False))
        widget.stateChanged.connect(self.configChanged.emit)
        self.widgets[name] = widget
        self.form_layout.addRow("", widget)

    def _add_file_widget(self, name, label):
        widget = QLineEdit()
        widget.setText(getattr(self.config, name, ""))
        widget.textChanged.connect(self.configChanged.emit)

        btn = QPushButton("📂")
        btn.setMaximumWidth(40)
        btn.clicked.connect(lambda: self._pick_file(widget))

        layout = QHBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(btn)

        self.widgets[name] = widget
        self.form_layout.addRow(label, layout)

    def _pick_file(self, line_edit):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            line_edit.setText(path)

    # --- Data Sync ---
    def update_config_from_widgets(self):
        """Update self.config based on widget values."""
        c = self.config
        w = self.widgets

        c.manga_title = w["manga_title"].text()
        c.zoom_factor = w["zoom_factor"].value()
        c.vertical_offset = w["vertical_offset"].value()
        c.cols = w["cols"].value()
        c.title_row_height = w["title_row_height"].value()
        c.vertical_padding = w["vertical_padding"].value()
        c.bottom_margin = w["bottom_margin"].value()
        c.horizontal_padding = w["horizontal_padding"].value()
        c.column_spacing = w["column_spacing"].value()
        c.title_fontsize = w["title_fontsize"].value()
        c.title_fontweight = w["title_fontweight"].currentText()
        c.title_color = w["title_color"].text()
        c.title_fontfamily = w["title_fontfamily"].text()
        c.date_fontsize = w["date_fontsize"].value()
        c.volume_fontsize = w["volume_fontsize"].value()
        c.text_color = w["text_color"].text()
        c.background_color = w["background_color"].text()
        c.frame_border_color = w["frame_border_color"].text()
        c.background_lineart_enabled = w["background_lineart_enabled"].isChecked()
        c.background_lineart_path = w["background_lineart_path"].text()
        c.background_lineart_alpha = w["background_lineart_alpha"].value()
        c.output_dir = w["output_dir"].text()
        c.dpi = w["dpi"].value()

        # Sub-presets
        c.shape_preset["type"] = w["shape_type"].currentText()
        c.shape_preset["width"] = w["shape_width"].value()
        c.shape_preset["height"] = w["shape_height"].value()
        c.shape_preset["spacing"] = w["shape_spacing"].value()
        c.shape_preset["border_color"] = w["shape_border_color"].text()
        c.shape_preset["shadow_alpha"] = w["shape_shadow_alpha"].value()
        c.shape_preset["skew_angle"] = w["shape_skew_angle"].value()
        c.shape_preset["rotation_angle"] = w["shape_rotation_angle"].value()

        c.stagger_preset["type"] = w["stagger_type"].currentText()
        c.stagger_preset["offset"] = w["stagger_offset"].value()

    def set_config(self, new_config):
        """Update widgets to reflect a new config object."""
        self.config = new_config
        # This part needs to update all widgets... (omitted for brevity, can implement if needed or just rely on manual update for now)
        # For now, let's just trigger update logic from main window if needed
        # Actually, we need to populate widgets from config to support loading presets.
        # I'll implement a basic version.
        self._update_widgets_from_config_obj()

    def _update_widgets_from_config_obj(self):
        c = self.config
        w = self.widgets

        # Simple fields
        if "manga_title" in w:
            w["manga_title"].setText(c.manga_title)
        if "zoom_factor" in w:
            w["zoom_factor"].setValue(c.zoom_factor)
        if "vertical_offset" in w:
            w["vertical_offset"].setValue(c.vertical_offset)
        if "cols" in w:
            w["cols"].setValue(c.cols)
        if "title_row_height" in w:
            w["title_row_height"].setValue(c.title_row_height)
        if "vertical_padding" in w:
            w["vertical_padding"].setValue(c.vertical_padding)
        if "bottom_margin" in w:
            w["bottom_margin"].setValue(c.bottom_margin)
        if "horizontal_padding" in w:
            w["horizontal_padding"].setValue(c.horizontal_padding)
        if "column_spacing" in w:
            w["column_spacing"].setValue(c.column_spacing)

        # Title
        if "title_fontsize" in w:
            w["title_fontsize"].setValue(c.title_fontsize)
        if "title_fontweight" in w:
            w["title_fontweight"].setCurrentText(c.title_fontweight)
        if "title_color" in w:
            w["title_color"].setText(c.title_color)
        if "title_fontfamily" in w:
            w["title_fontfamily"].setText(c.title_fontfamily)

        # Text
        if "date_fontsize" in w:
            w["date_fontsize"].setValue(c.date_fontsize)
        if "volume_fontsize" in w:
            w["volume_fontsize"].setValue(c.volume_fontsize)
        if "text_color" in w:
            w["text_color"].setText(c.text_color)

        # Background
        if "background_color" in w:
            w["background_color"].setText(c.background_color)
        if "frame_border_color" in w:
            w["frame_border_color"].setText(c.frame_border_color)

        # Lineart
        if "background_lineart_enabled" in w:
            w["background_lineart_enabled"].setChecked(c.background_lineart_enabled)
        if "background_lineart_path" in w:
            w["background_lineart_path"].setText(c.background_lineart_path)
        if "background_lineart_alpha" in w:
            w["background_lineart_alpha"].setValue(c.background_lineart_alpha)

        # Output
        if "output_dir" in w:
            w["output_dir"].setText(c.output_dir)
        if "dpi" in w:
            w["dpi"].setValue(c.dpi)

        # Shape preset
        if "shape_type" in w:
            w["shape_type"].setCurrentText(c.shape_preset.get("type", "parallelogram"))
        if "shape_width" in w:
            w["shape_width"].setValue(c.shape_preset.get("width", 1.5))
        if "shape_height" in w:
            w["shape_height"].setValue(c.shape_preset.get("height", 2.5))
        if "shape_spacing" in w:
            w["shape_spacing"].setValue(c.shape_preset.get("spacing", 0.0))
        if "shape_border_color" in w:
            w["shape_border_color"].setText(c.shape_preset.get("border_color", "gold"))
        if "shape_shadow_alpha" in w:
            w["shape_shadow_alpha"].setValue(c.shape_preset.get("shadow_alpha", 0.4))
        if "shape_skew_angle" in w:
            w["shape_skew_angle"].setValue(c.shape_preset.get("skew_angle", -15))
        if "shape_rotation_angle" in w:
            w["shape_rotation_angle"].setValue(c.shape_preset.get("rotation_angle", 0))

        # Stagger preset
        if "stagger_type" in w:
            w["stagger_type"].setCurrentText(c.stagger_preset.get("type", "none"))
        if "stagger_offset" in w:
            w["stagger_offset"].setValue(c.stagger_preset.get("offset", 0.1))
