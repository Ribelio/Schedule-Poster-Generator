from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap


class PreviewPanel(QWidget):
    """
    Panel for displaying the generated poster preview.
    Handles loading states and resizing.
    """

    def __init__(self):
        super().__init__()
        self._current_pixmap = None
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
        self.preview_label.setStyleSheet(
            "background-color: #1a1a1a; border: 1px solid #333; color: #888;"
        )

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
        if pixmap.isNull():
            self.show_error("Failed to load image")
            return
        
        # Store the original pixmap for resizing
        self._current_pixmap = pixmap
        self._scale_and_display()
    
    def _scale_and_display(self):
        """Scale the stored pixmap to fit and display it."""
        if self._current_pixmap is None or self._current_pixmap.isNull():
            return
        
        # Get available size from scroll area viewport
        scroll_size = self.scroll_area.viewport().size()
        if scroll_size.width() <= 0 or scroll_size.height() <= 0:
            # Fallback to label minimum size if scroll area not ready
            scroll_size = self.preview_label.minimumSize()
        
        # Scale to fit while maintaining aspect ratio
        # Leave some padding
        available_width = max(scroll_size.width() - 20, 100)
        available_height = max(scroll_size.height() - 20, 100)
        
        scaled_pixmap = self._current_pixmap.scaled(
            available_width, available_height, 
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        # Clear text first to avoid overlap
        self.preview_label.clear()
        self.preview_label.setPixmap(scaled_pixmap)
        
        # Update style without clearing pixmap
        self.preview_label.setStyleSheet(
            "background-color: #1a1a1a; border: 1px solid #333;"
        )
    
    def resizeEvent(self, event):
        """Handle resize events to update image scaling."""
        super().resizeEvent(event)
        if self._current_pixmap is not None:
            # Use a small delay to avoid excessive rescaling during resize
            QTimer.singleShot(50, self._scale_and_display)
