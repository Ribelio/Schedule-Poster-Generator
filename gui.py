"""
GUI editor for the Schedule Poster Generator using PySide6.
"""

import sys
from io import BytesIO
from typing import Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QScrollArea, QLabel, QPushButton, QDoubleSpinBox, QSpinBox,
    QComboBox, QLineEdit, QColorDialog, QCheckBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPalette, QColor

from config import PosterConfig, schedule, cover_urls, config as default_config
from renderer import render_poster_to_buffer, create_poster
from manga_fetcher import MangaDexFetcher


class PosterEditor(QMainWindow):
    """Main GUI window for editing poster configuration."""
    
    def __init__(self):
        super().__init__()
        self.config = PosterConfig()
        self.cover_data = {}
        self.widgets: Dict[str, Any] = {}
        
        self.setWindowTitle("Schedule Poster Generator - Editor")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply dark theme
        self._apply_dark_theme()
        
        # Initialize cover data
        self._fetch_covers()
        
        # Setup UI
        self._setup_ui()
        
        # Initial preview
        self.refresh_preview()
    
    def _apply_dark_theme(self):
        """Apply dark theme matching the poster aesthetic."""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(26, 26, 26))  # #1a1a1a
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(40, 40, 40))
        palette.setColor(QPalette.AlternateBase, QColor(50, 50, 50))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(60, 60, 60))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        self.setPalette(palette)
        
        # Additional stylesheet for better appearance
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QScrollArea {
                border: 1px solid #333;
                background-color: #1a1a1a;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #555;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QDoubleSpinBox, QSpinBox, QLineEdit, QComboBox {
                background-color: #2a2a2a;
                border: 1px solid #555;
                padding: 4px;
                color: white;
                border-radius: 3px;
            }
            QCheckBox {
                color: white;
            }
            QFormLayout {
                spacing: 10px;
            }
        """)
    
    def _fetch_covers(self):
        """Fetch covers from MangaDex API once at startup."""
        print(f"\nFetching covers for {self.config.manga_title}...")
        fetcher = MangaDexFetcher()
        
        # Extract unique volumes from schedule
        unique_volumes = set()
        for _, vols in schedule:
            unique_volumes.update(vols)
        
        mangadex_covers = fetcher.fetch_covers(self.config.manga_title, unique_volumes)
        
        # Merge with manual overrides
        self.cover_data = {**mangadex_covers, **cover_urls}
        print(f"Loaded {len(self.cover_data)} cover URL(s)\n")
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left panel: Preview canvas
        self._setup_preview_panel(main_layout)
        
        # Right panel: Inspector
        self._setup_inspector_panel(main_layout)
    
    def _setup_preview_panel(self, main_layout):
        """Setup the left panel with preview canvas."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)
        
        preview_label = QLabel()
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setScaledContents(False)
        preview_label.setMinimumSize(600, 400)
        preview_label.setText("Loading preview...")
        preview_label.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333;")
        
        self.preview_label = preview_label
        scroll_area.setWidget(preview_label)
        
        main_layout.addWidget(scroll_area, stretch=2)
    
    def _setup_inspector_panel(self, main_layout):
        """Setup the right panel with configuration widgets."""
        inspector_widget = QWidget()
        inspector_layout = QVBoxLayout(inspector_widget)
        
        # Scrollable form area
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create widgets for all config fields
        self._create_config_widgets(form_layout)
        
        form_scroll.setWidget(form_widget)
        inspector_layout.addWidget(form_scroll)
        
        # Export button at bottom
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
        export_btn.clicked.connect(self._export_to_disk)
        inspector_layout.addWidget(export_btn)
        
        main_layout.addWidget(inspector_widget, stretch=1)
    
    def _create_config_widgets(self, form_layout):
        """Auto-generate widgets for all PosterConfig fields."""
        # Manga title
        self._add_string_widget(form_layout, "manga_title", "Manga Title")
        
        # Image processing
        form_layout.addRow(QLabel("<b>Image Processing</b>"))
        self._add_float_widget(form_layout, "zoom_factor", "Zoom Factor", 0.1, 3.0, 0.1)
        self._add_float_widget(form_layout, "vertical_offset", "Vertical Offset", -1.0, 1.0, 0.01)
        
        # Layout settings
        form_layout.addRow(QLabel("<b>Layout</b>"))
        self._add_int_widget(form_layout, "cols", "Columns", 1, 10)
        self._add_float_widget(form_layout, "title_row_height", "Title Row Height", 0.5, 10.0, 0.1)
        self._add_float_widget(form_layout, "vertical_padding", "Vertical Padding", 0.0, 5.0, 0.1)
        self._add_float_widget(form_layout, "bottom_margin", "Bottom Margin", 0.0, 5.0, 0.1)
        self._add_float_widget(form_layout, "horizontal_padding", "Horizontal Padding", 0.0, 5.0, 0.1)
        self._add_float_widget(form_layout, "column_spacing", "Column Spacing", 0.0, 5.0, 0.1)
        
        # Shape preset
        form_layout.addRow(QLabel("<b>Frame Shape</b>"))
        self._add_shape_type_widget(form_layout)
        self._add_float_widget(form_layout, "shape_width", "Frame Width", 0.5, 10.0, 0.1)
        self._add_float_widget(form_layout, "shape_height", "Frame Height", 0.5, 10.0, 0.1)
        self._add_float_widget(form_layout, "shape_spacing", "Frame Spacing", 0.0, 5.0, 0.1)
        self._add_color_widget(form_layout, "shape_border_color", "Border Color")
        self._add_float_widget(form_layout, "shape_shadow_alpha", "Shadow Alpha", 0.0, 1.0, 0.05)
        self._add_float_widget(form_layout, "shape_skew_angle", "Skew Angle", -90.0, 90.0, 1.0)
        self._add_float_widget(form_layout, "shape_rotation_angle", "Rotation Angle", -180.0, 180.0, 1.0)
        
        # Stagger preset
        form_layout.addRow(QLabel("<b>Stagger</b>"))
        self._add_stagger_type_widget(form_layout)
        self._add_float_widget(form_layout, "stagger_offset", "Stagger Offset", 0.0, 2.0, 0.1)
        
        # Title settings
        form_layout.addRow(QLabel("<b>Title</b>"))
        self._add_int_widget(form_layout, "title_fontsize", "Title Font Size", 10, 100)
        self._add_fontweight_widget(form_layout)
        self._add_color_widget(form_layout, "title_color", "Title Color")
        self._add_string_widget(form_layout, "title_fontfamily", "Title Font Family")
        
        # Text settings
        form_layout.addRow(QLabel("<b>Text</b>"))
        self._add_int_widget(form_layout, "date_fontsize", "Date Font Size", 8, 50)
        self._add_int_widget(form_layout, "volume_fontsize", "Volume Font Size", 8, 50)
        self._add_color_widget(form_layout, "text_color", "Text Color")
        
        # Colors
        form_layout.addRow(QLabel("<b>Colors</b>"))
        self._add_color_widget(form_layout, "background_color", "Background Color")
        self._add_color_widget(form_layout, "frame_border_color", "Frame Border Color")
        
        # Background line art
        form_layout.addRow(QLabel("<b>Background Line Art</b>"))
        self._add_bool_widget(form_layout, "background_lineart_enabled", "Enabled")
        self._add_file_widget(form_layout, "background_lineart_path", "Image Path")
        self._add_float_widget(form_layout, "background_lineart_alpha", "Alpha", 0.0, 1.0, 0.05)
        
        # Output settings
        form_layout.addRow(QLabel("<b>Output</b>"))
        self._add_string_widget(form_layout, "output_dir", "Output Directory")
        self._add_int_widget(form_layout, "dpi", "DPI", 50, 600)
    
    def _add_string_widget(self, form_layout, field_name, label):
        """Add a string input widget."""
        widget = QLineEdit()
        widget.setText(str(getattr(self.config, field_name, "")))
        widget.textChanged.connect(self.refresh_preview)
        form_layout.addRow(label, widget)
        self.widgets[field_name] = widget
    
    def _add_int_widget(self, form_layout, field_name, label, min_val=1, max_val=1000):
        """Add an integer spinbox widget."""
        widget = QSpinBox()
        widget.setRange(min_val, max_val)
        widget.setValue(getattr(self.config, field_name, min_val))
        widget.valueChanged.connect(self.refresh_preview)
        form_layout.addRow(label, widget)
        self.widgets[field_name] = widget
    
    def _add_float_widget(self, form_layout, field_name, label, min_val=0.0, max_val=100.0, step=0.1):
        """Add a float spinbox widget."""
        widget = QDoubleSpinBox()
        widget.setRange(min_val, max_val)
        widget.setSingleStep(step)
        widget.setDecimals(2)
        # Handle nested preset fields
        if field_name.startswith('shape_'):
            preset_key = field_name.replace('shape_', '')
            if preset_key == 'width':
                value = self.config.shape_preset.get('width', min_val)
            elif preset_key == 'height':
                value = self.config.shape_preset.get('height', min_val)
            elif preset_key == 'spacing':
                value = self.config.shape_preset.get('spacing', min_val)
            elif preset_key == 'shadow_alpha':
                value = self.config.shape_preset.get('shadow_alpha', min_val)
            elif preset_key == 'skew_angle':
                value = self.config.shape_preset.get('skew_angle', min_val)
            elif preset_key == 'rotation_angle':
                value = self.config.shape_preset.get('rotation_angle', min_val)
            else:
                value = getattr(self.config, field_name, min_val)
        elif field_name.startswith('stagger_'):
            preset_key = field_name.replace('stagger_', '')
            value = self.config.stagger_preset.get(preset_key, min_val)
        else:
            value = getattr(self.config, field_name, min_val)
        widget.setValue(value)
        widget.valueChanged.connect(self.refresh_preview)
        form_layout.addRow(label, widget)
        self.widgets[field_name] = widget
    
    def _add_bool_widget(self, form_layout, field_name, label):
        """Add a checkbox widget."""
        widget = QCheckBox()
        widget.setChecked(getattr(self.config, field_name, False))
        widget.stateChanged.connect(self.refresh_preview)
        form_layout.addRow(label, widget)
        self.widgets[field_name] = widget
    
    def _add_color_widget(self, form_layout, field_name, label):
        """Add a color picker widget."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        color_edit = QLineEdit()
        # Handle nested preset fields
        if field_name == 'shape_border_color':
            value = self.config.shape_preset.get('border_color', '#ffffff')
        else:
            value = getattr(self.config, field_name, "#ffffff")
        color_edit.setText(value)
        color_edit.textChanged.connect(self.refresh_preview)
        
        color_btn = QPushButton("🎨")
        color_btn.setMaximumWidth(40)
        color_btn.clicked.connect(lambda: self._pick_color(field_name, color_edit))
        
        layout.addWidget(color_edit)
        layout.addWidget(color_btn)
        
        form_layout.addRow(label, container)
        self.widgets[field_name] = color_edit
    
    def _add_shape_type_widget(self, form_layout):
        """Add shape type combobox."""
        widget = QComboBox()
        widget.addItems(['parallelogram', 'rhombus', 'rectangle', 'hexagon'])
        current_type = self.config.shape_preset.get('type', 'parallelogram')
        widget.setCurrentText(current_type)
        widget.currentTextChanged.connect(self.refresh_preview)
        form_layout.addRow("Shape Type", widget)
        self.widgets['shape_type'] = widget
    
    def _add_stagger_type_widget(self, form_layout):
        """Add stagger type combobox."""
        widget = QComboBox()
        widget.addItems(['none', 'alternating', 'staircase'])
        current_type = self.config.stagger_preset.get('type', 'none')
        widget.setCurrentText(current_type)
        widget.currentTextChanged.connect(self.refresh_preview)
        form_layout.addRow("Stagger Type", widget)
        self.widgets['stagger_type'] = widget
    
    def _add_fontweight_widget(self, form_layout):
        """Add font weight combobox."""
        widget = QComboBox()
        widget.addItems(['normal', 'bold', 'light'])
        widget.setCurrentText(self.config.title_fontweight)
        widget.currentTextChanged.connect(self.refresh_preview)
        form_layout.addRow("Title Font Weight", widget)
        self.widgets['title_fontweight'] = widget
    
    def _add_file_widget(self, form_layout, field_name, label):
        """Add a file path widget."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        file_edit = QLineEdit()
        file_edit.setText(getattr(self.config, field_name, ""))
        file_edit.textChanged.connect(self.refresh_preview)
        
        file_btn = QPushButton("📁")
        file_btn.setMaximumWidth(40)
        file_btn.clicked.connect(lambda: self._pick_file(field_name, file_edit))
        
        layout.addWidget(file_edit)
        layout.addWidget(file_btn)
        
        form_layout.addRow(label, container)
        self.widgets[field_name] = file_edit
    
    def _pick_color(self, field_name, color_edit):
        """Open color picker dialog."""
        current_color = QColor(color_edit.text())
        color = QColorDialog.getColor(current_color, self, "Pick Color")
        if color.isValid():
            color_edit.setText(color.name())
    
    def _pick_file(self, field_name, file_edit):
        """Open file picker dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", file_edit.text(),
            "Image Files (*.png *.jpg *.jpeg);;All Files (*)"
        )
        if file_path:
            file_edit.setText(file_path)
    
    def _update_config_from_widgets(self):
        """Update config object from widget values."""
        # Simple fields
        self.config.manga_title = self.widgets['manga_title'].text()
        self.config.zoom_factor = self.widgets['zoom_factor'].value()
        self.config.vertical_offset = self.widgets['vertical_offset'].value()
        self.config.cols = self.widgets['cols'].value()
        self.config.title_row_height = self.widgets['title_row_height'].value()
        self.config.vertical_padding = self.widgets['vertical_padding'].value()
        self.config.bottom_margin = self.widgets['bottom_margin'].value()
        self.config.horizontal_padding = self.widgets['horizontal_padding'].value()
        self.config.column_spacing = self.widgets['column_spacing'].value()
        self.config.title_fontsize = self.widgets['title_fontsize'].value()
        self.config.title_fontweight = self.widgets['title_fontweight'].currentText()
        self.config.title_color = self.widgets['title_color'].text()
        self.config.title_fontfamily = self.widgets['title_fontfamily'].text()
        self.config.date_fontsize = self.widgets['date_fontsize'].value()
        self.config.volume_fontsize = self.widgets['volume_fontsize'].value()
        self.config.text_color = self.widgets['text_color'].text()
        self.config.background_color = self.widgets['background_color'].text()
        self.config.frame_border_color = self.widgets['frame_border_color'].text()
        self.config.background_lineart_enabled = self.widgets['background_lineart_enabled'].isChecked()
        self.config.background_lineart_path = self.widgets['background_lineart_path'].text()
        self.config.background_lineart_alpha = self.widgets['background_lineart_alpha'].value()
        self.config.output_dir = self.widgets['output_dir'].text()
        self.config.dpi = self.widgets['dpi'].value()
        
        # Shape preset
        self.config.shape_preset['type'] = self.widgets['shape_type'].currentText()
        self.config.shape_preset['width'] = self.widgets['shape_width'].value()
        self.config.shape_preset['height'] = self.widgets['shape_height'].value()
        self.config.shape_preset['spacing'] = self.widgets['shape_spacing'].value()
        self.config.shape_preset['border_color'] = self.widgets['shape_border_color'].text()
        self.config.shape_preset['shadow_alpha'] = self.widgets['shape_shadow_alpha'].value()
        self.config.shape_preset['skew_angle'] = self.widgets['shape_skew_angle'].value()
        self.config.shape_preset['rotation_angle'] = self.widgets['shape_rotation_angle'].value()
        
        # Stagger preset
        self.config.stagger_preset['type'] = self.widgets['stagger_type'].currentText()
        self.config.stagger_preset['offset'] = self.widgets['stagger_offset'].value()
    
    def refresh_preview(self):
        """Update the preview image based on current widget values."""
        try:
            # Update config from widgets
            self._update_config_from_widgets()
            
            # Render to buffer
            buffer = render_poster_to_buffer(self.config, self.cover_data, schedule)
            
            # Convert to QPixmap
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            
            # Scale to fit while maintaining aspect ratio
            label_size = self.preview_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            self.preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            self.preview_label.setText(f"Error: {str(e)}")
            print(f"Preview error: {e}")
    
    def _export_to_disk(self):
        """Export the current poster to disk."""
        try:
            self._update_config_from_widgets()
            output_path = create_poster(self.config)
            self.preview_label.setText(f"Saved to:\n{output_path}")
        except Exception as e:
            self.preview_label.setText(f"Export error: {str(e)}")
            print(f"Export error: {e}")


def main():
    """Main entry point for the GUI application."""
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    editor = PosterEditor()
    editor.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

