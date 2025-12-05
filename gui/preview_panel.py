from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class PreviewPanel(QWidget):
    """
    Panel for displaying the generated poster preview.
    Handles loading states and resizing.
    """
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setScaledContents(False)
        self.preview_label.setMinimumSize(600, 400)
        self.preview_label.setText("Loading preview...")
        self._set_default_style()
        
        self.scroll_area.setWidget(self.preview_label)
        layout.addWidget(self.scroll_area)

    def _set_default_style(self):
        self.preview_label.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333; color: #888;")

    def show_loading(self):
        self.preview_label.setText("Loading preview...\nPlease wait")
        self.preview_label.setStyleSheet("""
            background-color: #1a1a1a; 
            border: 1px solid #333;
            color: white;
            font-size: 14px;
        """)

    def show_error(self, message: str):
        self.preview_label.setText(f"Error: {message}")
        self.preview_label.setStyleSheet("""
            background-color: #1a1a1a; 
            border: 1px solid #333;
            color: #ff4444;
        """)

    def update_image(self, pixmap: QPixmap):
        # Scale to fit while maintaining aspect ratio
        label_size = self.preview_label.size()
        scaled_pixmap = pixmap.scaled(
            label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)
        self._set_default_style()



