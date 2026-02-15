"""Dialog listing past analysis runs with Load/Delete actions."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui.history_manager import HistoryManager
from mcpower_gui.theme import current_colors


class HistoryDialog(QDialog):
    """Scrollable list of history entries with Load and Delete buttons.

    Emits ``load_requested(dict)`` with the full record when Load is clicked.
    """

    load_requested = Signal(dict)

    def __init__(self, history: HistoryManager, parent: QWidget | None = None):
        super().__init__(parent)
        self._history = history
        self.setWindowTitle("Analysis History")
        self.resize(600, 450)

        root = QVBoxLayout(self)

        # Scrollable list
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        root.addWidget(self._scroll, stretch=1)

        self._rebuild_list()

        # Close button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        root.addWidget(btn_close)

    def _rebuild_list(self):
        """(Re)build the list of history entries."""
        container = QWidget()
        layout = QVBoxLayout(container)

        records = self._history.list_records()
        if not records:
            placeholder = QLabel("No history entries yet.")
            placeholder.setStyleSheet(
                f"color: {current_colors()['muted']}; padding: 20px;"
            )
            layout.addWidget(placeholder)
        else:
            for rec in records:
                layout.addWidget(self._make_entry(rec))

        layout.addStretch()
        self._scroll.setWidget(container)

    def _make_entry(self, rec: dict) -> QWidget:
        """Create a single history entry widget."""
        entry = QWidget()
        colors = current_colors()
        entry.setStyleSheet(
            f"QWidget {{ border: 1px solid {colors['border']}; border-radius: 4px; "
            f"padding: 6px; margin: 2px; }}"
        )
        row = QHBoxLayout(entry)

        # Info column
        info = QVBoxLayout()
        mode_label = "Find Power" if rec["mode"] == "power" else "Find Sample Size"
        ts = rec.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            ts_display = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            ts_display = ts[:16] if ts else "?"

        title = QLabel(f"<b>{mode_label}</b> — {ts_display}")
        info.addWidget(title)

        formula = rec.get("formula", "")
        test_formula = rec.get("test_formula", "")
        correction = rec.get("correction", "")
        scenarios = rec.get("scenarios", False)

        detail_parts = []
        if formula:
            detail_parts.append(f"model formula: {formula}")
        if test_formula:
            detail_parts.append(f"test formula: {test_formula}")

        if rec["mode"] == "power":
            ss = rec.get("sample_size")
            if ss is not None:
                detail_parts.append(f"N = {ss}")
        else:
            ss_from = rec.get("ss_from")
            ss_to = rec.get("ss_to")
            ss_by = rec.get("ss_by")
            if ss_from is not None:
                detail_parts.append(f"from {ss_from} to {ss_to}, by {ss_by}")

        if scenarios:
            detail_parts.append("scenarios")
        if correction:
            detail_parts.append(f"correction: {correction}")

        detail = QLabel(" | ".join(detail_parts))
        detail.setStyleSheet(f"color: {current_colors()['muted']}; font-size: 11px;")
        detail.setWordWrap(True)
        info.addWidget(detail)
        row.addLayout(info, stretch=1)

        # Buttons column
        btn_col = QVBoxLayout()
        btn_load = QPushButton("Load")
        btn_load.setFixedWidth(70)
        record_id = rec["id"]
        btn_load.clicked.connect(
            lambda checked=False, rid=record_id: self._on_load(rid)
        )
        btn_col.addWidget(btn_load)

        btn_delete = QPushButton("Delete")
        btn_delete.setFixedWidth(70)
        btn_delete.clicked.connect(
            lambda checked=False, rid=record_id: self._on_delete(rid)
        )
        btn_col.addWidget(btn_delete)
        row.addLayout(btn_col)

        return entry

    def _on_load(self, record_id: str):
        record = self._history.load(record_id)
        if record is None:
            QMessageBox.warning(self, "Error", "History record not found.")
            return
        self.load_requested.emit(record)
        self.close()

    def _on_delete(self, record_id: str):
        self._history.delete(record_id)
        self._rebuild_list()
