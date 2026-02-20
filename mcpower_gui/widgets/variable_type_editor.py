"""Per-predictor variable type editor — continuous / binary / factor."""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui.widgets.spin_boxes import DoubleSpinBox, SpinBox


class VariableTypeEditor(QWidget):
    """Widget with one row per predictor for configuring variable types.

    Each row has: label | type combo | conditional params (proportion / levels+proportions).

    Emits ``types_changed(dict)`` whenever any value changes.
    The dict maps predictor name -> info dict with keys:
      - "type": "continuous" | "binary" | "factor"
      - "proportion": float  (binary only)
      - "n_levels": int  (factor only)
      - "proportions": list[float]  (factor only)
    """

    types_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: dict[str, _PredictorRow] = {}

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def set_predictors(self, predictors: list[str], current_types: dict[str, dict]):
        """Rebuild rows for a new predictor list, preserving existing type configs."""
        # Clear old rows
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rows.clear()

        # Compute dynamic label width from predictor names
        fm = self.fontMetrics()
        label_width = 120
        for name in predictors:
            w = fm.horizontalAdvance(name) + 12
            if w > label_width:
                label_width = w
        label_width = min(label_width, 250)

        for name in predictors:
            existing = current_types.get(name, {})
            row = _PredictorRow(name, existing, label_width=label_width)
            row.changed.connect(self._emit)
            self._rows[name] = row
            self._layout.addWidget(row)

    def set_data_detected_types(self, detected: dict[str, dict]):
        """Enable/disable data-upload mode on matching rows."""
        for name, row in self._rows.items():
            if name in detected:
                row.set_data_mode(detected[name])
            else:
                row.clear_data_mode()

    def get_types(self) -> dict[str, dict]:
        """Return current type configuration for all predictors."""
        return {name: row.get_info() for name, row in self._rows.items()}

    def _emit(self):
        self.types_changed.emit(self.get_types())


class _PredictorRow(QWidget):
    """Single row: [label 120px] [type combo] [conditional params]."""

    changed = Signal()

    def __init__(self, name: str, existing: dict, parent=None, label_width: int = 120):
        super().__init__(parent)
        self._name = name
        self._proportion_spin: QDoubleSpinBox | None = None
        self._levels_spin: QSpinBox | None = None
        self._factor_proportions: list[QDoubleSpinBox] = []
        self._factor_container: QWidget | None = None
        self._suppress_signals = False
        self._data_mode = False
        self._level_labels: list[str] | None = existing.get("level_labels")

        h = QHBoxLayout(self)
        h.setContentsMargins(0, 2, 0, 2)

        label = QLabel(name)
        label.setFixedWidth(label_width)
        label.setToolTip(name)
        h.addWidget(label)

        self._type_combo = QComboBox()
        self._type_combo.addItems(["continuous", "binary", "factor"])
        self._type_combo.setFixedWidth(110)
        h.addWidget(self._type_combo)

        # Params area — stacked vertically to the right of the combo
        self._params_area = QVBoxLayout()
        self._params_area.setContentsMargins(4, 0, 0, 0)
        h.addLayout(self._params_area, stretch=1)

        # Restore from existing info
        vtype = existing.get("type", "continuous")
        self._type_combo.setCurrentText(vtype)
        self._rebuild_params(vtype, existing)

        self._type_combo.currentTextChanged.connect(self._on_type_changed)

    def _on_type_changed(self, vtype: str):
        self._rebuild_params(vtype, {})
        self.changed.emit()

    def set_data_mode(self, info: dict):
        """Enable data-upload mode: lock type combo, hide proportions."""
        self._data_mode = True
        self._type_combo.setEnabled(False)
        self._hide_proportion_widgets()
        if "level_labels" in info:
            self._level_labels = info["level_labels"]

    def clear_data_mode(self):
        """Disable data-upload mode: re-enable type combo."""
        if not self._data_mode:
            return
        self._data_mode = False
        self._type_combo.setEnabled(True)

    def _hide_proportion_widgets(self):
        """Hide proportion-related widgets in data mode."""
        if self._proportion_spin is not None:
            self._proportion_spin.parent().hide()
        if self._factor_container is not None:
            self._factor_container.hide()
        if self._levels_spin is not None:
            self._levels_spin.parent().hide()

    def _rebuild_params(self, vtype: str, existing: dict):
        """Rebuild the conditional parameter widgets for the current type."""
        # Clear params area
        while self._params_area.count():
            item = self._params_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._proportion_spin = None
        self._levels_spin = None
        self._factor_proportions = []
        self._factor_container = None

        if vtype == "binary":
            row = QWidget()
            rh = QHBoxLayout(row)
            rh.setContentsMargins(0, 0, 0, 0)
            rh.addWidget(QLabel("Proportion:"))
            self._proportion_spin = DoubleSpinBox()
            self._proportion_spin.setRange(0.01, 0.99)
            self._proportion_spin.setSingleStep(0.05)
            self._proportion_spin.setDecimals(2)
            self._proportion_spin.setValue(existing.get("proportion", 0.5))
            self._proportion_spin.setFixedWidth(70)
            self._proportion_spin.valueChanged.connect(lambda: self.changed.emit())
            rh.addWidget(self._proportion_spin)
            rh.addStretch()
            self._params_area.addWidget(row)

        elif vtype == "factor":
            # Levels spinner row
            levels_row = QWidget()
            lh = QHBoxLayout(levels_row)
            lh.setContentsMargins(0, 0, 0, 0)
            lh.addWidget(QLabel("Levels:"))
            self._levels_spin = SpinBox()
            self._levels_spin.setRange(2, 20)
            n_levels = existing.get("n_levels", 3)
            self._levels_spin.setValue(n_levels)
            self._levels_spin.setFixedWidth(60)
            self._levels_spin.valueChanged.connect(self._on_levels_changed)
            lh.addWidget(self._levels_spin)
            lh.addStretch()
            self._params_area.addWidget(levels_row)

            # Proportions row(s)
            self._factor_container = QWidget()
            self._factor_layout = QHBoxLayout(self._factor_container)
            self._factor_layout.setContentsMargins(0, 0, 0, 0)
            self._params_area.addWidget(self._factor_container)

            existing_props = existing.get("proportions", [])
            self._build_factor_proportions(n_levels, existing_props)

        # In data mode, hide proportion/levels widgets
        if self._data_mode:
            self._hide_proportion_widgets()

    def _on_levels_changed(self, n_levels: int):
        """Rebuild proportion spinboxes when number of levels changes."""
        self._build_factor_proportions(n_levels, [])
        self.changed.emit()

    def _build_factor_proportions(self, n_levels: int, existing_props: list[float]):
        """Create n_levels proportion spinboxes with equal defaults."""
        # Clear existing
        while self._factor_layout.count():
            item = self._factor_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._factor_proportions = []

        # Default: equal proportions
        if len(existing_props) == n_levels:
            props = list(existing_props)
        else:
            props = [round(1.0 / n_levels, 4)] * n_levels

        self._factor_layout.addWidget(QLabel("Proportions:"))
        for i in range(n_levels):
            spin = DoubleSpinBox()
            spin.setRange(0.01, 0.99)
            spin.setSingleStep(0.05)
            spin.setDecimals(2)
            spin.setValue(props[i] if i < len(props) else round(1.0 / n_levels, 4))
            spin.setFixedWidth(60)
            spin.setToolTip(f"Level {i + 1}")
            spin.valueChanged.connect(self._on_proportion_changed)
            self._factor_layout.addWidget(spin)
            self._factor_proportions.append(spin)

        normalize_btn = QPushButton("(to 100%)")
        normalize_btn.setFixedWidth(80)
        normalize_btn.setToolTip("Normalize proportions to sum to 1.0")
        normalize_btn.clicked.connect(self._normalize_proportions)
        self._factor_layout.addWidget(normalize_btn)
        self._factor_layout.addStretch()

    def _on_proportion_changed(self):
        """Emit changed without auto-normalizing."""
        if self._suppress_signals:
            return
        self.changed.emit()

    def _normalize_proportions(self):
        """Normalize factor proportions to sum to 1.0 (triggered by button)."""
        self._suppress_signals = True
        raw = [s.value() for s in self._factor_proportions]
        total = sum(raw)
        if total > 0:
            normalized = [round(v / total, 2) for v in raw]
            diff = round(1.0 - sum(normalized), 2)
            normalized[-1] = round(normalized[-1] + diff, 2)
            for spin, val in zip(self._factor_proportions, normalized):
                spin.setValue(val)
        self._suppress_signals = False
        self.changed.emit()

    def get_info(self) -> dict:
        """Return the type info dict for this predictor."""
        vtype = self._type_combo.currentText()
        info: dict = {"type": vtype}
        if vtype == "binary" and self._proportion_spin is not None:
            info["proportion"] = self._proportion_spin.value()
        elif vtype == "factor":
            if self._levels_spin is not None:
                info["n_levels"] = self._levels_spin.value()
            info["proportions"] = [s.value() for s in self._factor_proportions]
            if self._level_labels:
                info["level_labels"] = self._level_labels
        return info
