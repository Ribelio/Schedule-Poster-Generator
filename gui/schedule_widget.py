from typing import List, Tuple
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
)
from PySide6.QtCore import Signal


class ScheduleWidget(QWidget):
    """
    Widget for editing the schedule (dates and volumes).
    Emits scheduleChanged signal when data is modified.
    Emits fetchCoversRequested signal when fetch button is clicked.
    """

    scheduleChanged = Signal()
    fetchCoversRequested = Signal()

    def __init__(self, initial_schedule: List[Tuple[str, List[int]]] = None):
        super().__init__()
        self.schedule = initial_schedule or []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        layout.addWidget(QLabel("<b>Schedule</b>"))

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Date", "Volumes"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMaximumHeight(200)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellChanged.connect(self._on_cell_changed)

        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Add Row")
        add_btn.clicked.connect(self._add_row)

        remove_btn = QPushButton("➖ Remove Row")
        remove_btn.clicked.connect(self._remove_row)

        fetch_btn = QPushButton("🔄 Fetch Covers")
        fetch_btn.clicked.connect(self.fetchCoversRequested.emit)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(fetch_btn)

        layout.addLayout(btn_layout)

        self._populate_table()

    def _populate_table(self):
        """Populate table from self.schedule data."""
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.schedule))
        for row, (date, vols) in enumerate(self.schedule):
            # Date
            self.table.setItem(row, 0, QTableWidgetItem(date))
            # Volumes
            vol_str = ", ".join(map(str, vols))
            self.table.setItem(row, 1, QTableWidgetItem(vol_str))
        self.table.blockSignals(False)

    def _on_cell_changed(self, row, col):
        """Handle cell edits."""
        self._update_schedule_from_table()
        self.scheduleChanged.emit()

    def _update_schedule_from_table(self):
        """Parse table contents into self.schedule list."""
        new_schedule = []
        for row in range(self.table.rowCount()):
            date_item = self.table.item(row, 0)
            vol_item = self.table.item(row, 1)

            if not date_item or not vol_item:
                continue

            date = date_item.text().strip()
            vol_str = vol_item.text().strip()

            if date:
                try:
                    if vol_str:
                        vols = [
                            int(v.strip())
                            for v in vol_str.split(",")
                            if v.strip().isdigit()
                        ]
                    else:
                        vols = []
                    new_schedule.append((date, vols))
                except ValueError:
                    pass

        self.schedule = new_schedule

    def _add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(""))
        self.table.setItem(row, 1, QTableWidgetItem(""))
        self.table.selectRow(row)
        # We don't emit changed yet, wait for user to type

    def _remove_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self._update_schedule_from_table()
            self.scheduleChanged.emit()

    def get_schedule(self) -> List[Tuple[str, List[int]]]:
        return self.schedule

    def set_schedule(self, schedule: List[Tuple[str, List[int]]]):
        self.schedule = schedule
        self._populate_table()
