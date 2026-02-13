"""Lower-triangle grid editor for pairwise variable correlations."""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QWidget,
)


def _corr_key(a: str, b: str) -> str:
    """Canonical alphabetically-sorted correlation key."""
    return ",".join(sorted([a, b]))


class CorrelationEditor(QWidget):
    """Lower-triangle grid of spinboxes for pairwise correlations.

    Only continuous and binary variables can be correlated (NOT factors).
    """

    correlations_changed = Signal(dict)  # {canonical_key: float}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._variables: list[str] = []
        self._cells: dict[str, QDoubleSpinBox] = {}  # canonical key -> spinbox

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self._placeholder = QLabel("Need at least 2 correlable variables.")
        self._placeholder.setStyleSheet("color: gray;")
        self._grid.addWidget(self._placeholder, 0, 0)

    def set_variables(self, variables: list[str]):
        """Rebuild the grid for a new variable list, preserving existing values."""
        old_values = self.get_correlations()

        # Clear grid
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cells.clear()
        self._variables = list(variables)

        if len(variables) < 2:
            self._placeholder = QLabel("Need at least 2 correlable variables.")
            self._placeholder.setStyleSheet("color: gray;")
            self._grid.addWidget(self._placeholder, 0, 0)
            return

        n = len(variables)

        # Column headers (row 0, cols 1..n-1) — skip last var as it has no column
        for col_idx in range(n - 1):
            header = QLabel(variables[col_idx])
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setFixedWidth(65)
            self._grid.addWidget(header, 0, col_idx + 1)

        # Row headers and cells
        for row_idx in range(1, n):
            # Row header
            row_label = QLabel(variables[row_idx])
            row_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self._grid.addWidget(row_label, row_idx, 0)

            # Lower triangle cells: col < row
            for col_idx in range(row_idx):
                key = _corr_key(variables[row_idx], variables[col_idx])
                spin = QDoubleSpinBox()
                spin.setRange(-0.99, 0.99)
                spin.setSingleStep(0.05)
                spin.setDecimals(2)
                spin.setFixedWidth(65)
                spin.setValue(old_values.get(key, 0.0))
                spin.valueChanged.connect(lambda _, k=key: self._on_cell_changed())
                self._cells[key] = spin
                self._grid.addWidget(spin, row_idx, col_idx + 1)

    def set_correlations(self, correlations: dict[str, float]):
        """Populate cell values from a dict. Missing keys default to 0.0."""
        for key, spin in self._cells.items():
            spin.blockSignals(True)
            spin.setValue(correlations.get(key, 0.0))
            spin.blockSignals(False)

    def get_correlations(self) -> dict[str, float]:
        """Return non-zero correlation values."""
        return {
            key: spin.value()
            for key, spin in self._cells.items()
            if spin.value() != 0.0
        }

    def get_all_keys(self) -> list[str]:
        """Return all cell keys (including zero-valued cells)."""
        return list(self._cells.keys())

    def set_enabled(self, enabled: bool):
        """Enable or disable all spinboxes."""
        for spin in self._cells.values():
            spin.setEnabled(enabled)

    def set_locked_keys(self, locked_keys: set[str]):
        """Lock specific cells (disabled) while enabling the rest."""
        for key, spin in self._cells.items():
            spin.setEnabled(key not in locked_keys)

    def _on_cell_changed(self):
        self.correlations_changed.emit(self.get_correlations())
