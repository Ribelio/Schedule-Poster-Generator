from threading import Thread

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPixmap, QPalette, QColor

from config import PosterConfig, schedule, cover_urls
from renderer import render_poster_to_buffer
from manga_fetcher import MangaDexFetcher

from gui.preview_panel import PreviewPanel
from gui.settings_panel import SettingsPanel


class CoverFetchSignals(QObject):
    finished = Signal(object)  # Use object instead of dict for PySide6 compatibility
    error = Signal(str)


class PosterEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = PosterConfig()
        self.schedule = list(schedule)
        self.cover_data = {}
        self.current_manga_title = self.config.manga_title
        self.is_loading = False

        self._init_timers()
        self._init_ui()
        self._apply_dark_theme()

        # Initial fetch
        self._fetch_covers()

    def _init_timers(self):
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.refresh_preview)
        self.debounce_delay = 500

        self.loading_timer = QTimer()
        self.loading_timer.setSingleShot(True)
        self.loading_timer.timeout.connect(self._show_loading)

    def _init_ui(self):
        self.setWindowTitle("Schedule Poster Generator")
        self.setGeometry(100, 100, 1400, 900)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)

        # Panels
        self.preview_panel = PreviewPanel()
        self.settings_panel = SettingsPanel(self.config)

        # Initial schedule
        self.settings_panel.schedule_widget.set_schedule(self.schedule)

        layout.addWidget(self.preview_panel, stretch=2)
        layout.addWidget(self.settings_panel, stretch=1)

        # Connect signals
        self.settings_panel.configChanged.connect(self._trigger_update)
        self.settings_panel.configChanged.connect(self._update_row_heights)
        self.settings_panel.scheduleChanged.connect(self._trigger_update)
        self.settings_panel.scheduleChanged.connect(self._update_row_heights)
        self.settings_panel.titleConfirmed.connect(self._on_title_confirmed)
        self.settings_panel.fetchCoversRequested.connect(self._manual_fetch)
        self.settings_panel.savePresetRequested.connect(self._save_preset)
        self.settings_panel.loadPresetRequested.connect(self._load_preset)
        self.settings_panel.exportRequested.connect(self._export)
        
        # Initial row heights update
        self._update_row_heights()

    def _trigger_update(self):
        self.preview_timer.stop()
        self.loading_timer.stop()
        self.loading_timer.start(100)
        self.preview_timer.start(self.debounce_delay)
    
    def _on_title_confirmed(self):
        """Handle manga title confirmation - fetch new covers."""
        new_title = self.settings_panel.widgets["manga_title"].text().strip()
        if not new_title:
            return
        
        if new_title != self.current_manga_title:
            self.current_manga_title = new_title
            # Sync everything first
            self._sync_state()
            self._fetch_covers(new_title)

    def _sync_state(self):
        """Pull data from settings panel into self.config and self.schedule."""
        self.settings_panel.update_config_from_widgets()
        self.schedule = self.settings_panel.schedule_widget.get_schedule()
    
    def _update_row_heights(self):
        """Update row heights display."""
        self.settings_panel.update_row_heights_display(self.schedule)

    def _show_loading(self):
        if not self.is_loading:
            self.preview_panel.show_loading()

    def refresh_preview(self):
        try:
            self._sync_state()
            buffer = render_poster_to_buffer(
                self.config, self.cover_data, self.schedule
            )
            # Ensure buffer is at the start and get the data
            buffer.seek(0)
            buffer_data = buffer.getvalue()
            
            if not buffer_data or len(buffer_data) == 0:
                raise ValueError("Buffer is empty")
            
            pixmap = QPixmap()
            if not pixmap.loadFromData(buffer_data, "PNG"):
                # Try alternative loading method using QImage
                from PySide6.QtGui import QImage
                image = QImage()
                if image.loadFromData(buffer_data, "PNG"):
                    pixmap = QPixmap.fromImage(image)
                else:
                    raise ValueError("Failed to load image from buffer - invalid PNG data")
            
            if pixmap.isNull():
                raise ValueError("Pixmap is null after loading")
            
            self.preview_panel.update_image(pixmap)
        except Exception as e:
            self.preview_panel.show_error(str(e))
            print(f"Preview error: {e}")
            import traceback
            traceback.print_exc()

    # --- Fetching ---
    def _manual_fetch(self):
        self._sync_state()
        self._fetch_covers(self.config.manga_title)

    def _fetch_covers(self, title=None):
        title = title or self.config.manga_title
        vols = set()
        for _, v_list in self.schedule:
            vols.update(v_list)

        if not vols:
            return

        self.is_loading = True
        self._show_loading()

        signals = CoverFetchSignals()
        signals.finished.connect(self._on_fetch_done)
        signals.error.connect(self._on_fetch_error)

        Thread(
            target=self._fetch_thread, args=(title, vols, signals), daemon=True
        ).start()

    def _fetch_thread(self, title, vols, signals):
        try:
            print(f"Fetching covers for '{title}' (volumes: {sorted(vols)})...")
            f = MangaDexFetcher()
            covers = f.fetch_covers(title, vols)
            print(f"Found {len(covers)} cover(s) from MangaDex")
            merged = {**covers, **cover_urls}
            print(f"Total covers after merge: {len(merged)}")
            if merged:
                print(f"Cover URLs: {list(merged.keys())}")
            signals.finished.emit(merged)
        except Exception as e:
            print(f"Error in fetch thread: {e}")
            import traceback
            traceback.print_exc()
            signals.error.emit(str(e))

    def _on_fetch_done(self, covers):
        print(f"Fetch completed: {len(covers)} cover URL(s) received")
        self.cover_data = covers
        self.is_loading = False
        
        # Pre-download images in background to ensure they're cached
        # This helps ensure images are ready when rendering
        if covers:
            Thread(
                target=self._preload_images, args=(covers,), daemon=True
            ).start()
        
        self.refresh_preview()
    
    def _preload_images(self, covers):
        """Pre-load images in background to ensure they're cached."""
        from image_utils import load_image
        print(f"Pre-loading {len(covers)} images...")
        for vol, url in covers.items():
            if url:
                try:
                    img = load_image(url, volume=vol, manga_title=self.config.manga_title)
                    if img:
                        print(f"Pre-loaded volume {vol}")
                except Exception as e:
                    print(f"Warning: Failed to pre-load volume {vol}: {e}")
        print("Pre-loading complete")

    def _on_fetch_error(self, msg):
        self.is_loading = False
        self.preview_panel.show_error(f"Fetch failed: {msg}")

    # --- IO ---
    def _save_preset(self):
        self._sync_state()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Preset", "preset.json", "JSON (*.json)"
        )
        if path:
            self.config.save_to_json(path)

    def _load_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Preset", "", "JSON (*.json)")
        if path:
            self.config = PosterConfig.load_from_json(path)
            self.settings_panel.set_config(self.config)
            self._trigger_update()

    def _export(self):
        self._sync_state()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Poster", self.config.output_filename, "PNG (*.png)"
        )
        if path:
            if not path.lower().endswith(".png"):
                path += ".png"
            try:
                import os

                os.makedirs(
                    os.path.dirname(path) if os.path.dirname(path) else ".",
                    exist_ok=True,
                )
                buf = render_poster_to_buffer(
                    self.config, self.cover_data, self.schedule, "png"
                )
                with open(path, "wb") as f:
                    f.write(buf.getvalue())
                try:
                    os.startfile(path)
                except OSError:
                    pass
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(26, 26, 26))
        palette.setColor(QPalette.WindowText, Qt.white)
        self.setPalette(palette)
