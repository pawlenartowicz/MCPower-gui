"""ANOVA factor editor — replaces formula + variable type editors in ANOVA mode."""

from __future__ import annotations

from itertools import combinations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui.widgets.spin_boxes import DoubleSpinBox, SpinBox


class AnovaFactorEditor(QWidget):
    """Editor for ANOVA factors with dependent variable, dynamic factor rows,
    and interaction toggles.

    Emits the same signals as FormulaInput and VariableTypeEditor so that
    ModelTab can treat them uniformly.
    """

    formula_changed = Signal(str, str, list)  # formula, dep_var, predictors
    types_changed = Signal(dict)  # name -> type info dict

    def __init__(self, parent=None):
        super().__init__(parent)
        self._factor_rows: list[_FactorRow] = []
        self._interaction_checkboxes: list[tuple[str, QCheckBox]] = []
        self._suppress_signals = False
        self._last_factor_names: list[str] = []  # cache for interaction rebuild check
        self._data_mode = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Factor rows container
        self._factors_layout = QVBoxLayout()
        self._factors_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.addLayout(self._factors_layout)

        # Add Factor button
        self._btn_add = QPushButton("+ Add Factor")
        self._btn_add.setFixedWidth(120)
        self._btn_add.clicked.connect(self._add_factor)
        root.addWidget(self._btn_add)

        # Interactions section
        self._interactions_check = QCheckBox("Include interactions")
        self._interactions_check.toggled.connect(self._on_interactions_toggled)
        root.addWidget(self._interactions_check)

        self._interactions_container = QWidget()
        self._interactions_layout = QVBoxLayout(self._interactions_container)
        self._interactions_layout.setContentsMargins(20, 0, 0, 0)
        self._interactions_container.hide()
        root.addWidget(self._interactions_container)

        root.addStretch()

    # ── Public API ────────────────────────────────────────────

    def get_types(self) -> dict[str, dict]:
        """Return all-factor variable types dict for current factors."""
        types: dict[str, dict] = {}
        for row in self._factor_rows:
            name = row.get_name()
            if not name:
                continue
            n_levels = row.get_n_levels()
            proportions = row.get_proportions()
            info: dict = {
                "type": "factor",
                "n_levels": n_levels,
                "proportions": proportions,
            }
            level_labels = row.get_level_labels()
            if level_labels:
                info["level_labels"] = level_labels
            types[name] = info
        return types

    def get_factor_definitions(self) -> list[dict]:
        """Return raw factor definitions for state persistence."""
        defs = []
        for row in self._factor_rows:
            name = row.get_name()
            if not name:
                continue
            defs.append(
                {
                    "name": name,
                    "n_levels": row.get_n_levels(),
                    "proportions": row.get_proportions(),
                }
            )
        return defs

    def get_reference_levels(self) -> dict[str, str]:
        """Return {factor_name: reference_level} for factors with named levels."""
        refs = {}
        for row in self._factor_rows:
            name = row.get_name()
            ref = row.get_reference_level()
            if name and ref:
                refs[name] = ref
        return refs

    def get_level_labels(self) -> dict[str, list[str]]:
        """Return {factor_name: [labels]} for factors with named levels."""
        labels = {}
        for row in self._factor_rows:
            name = row.get_name()
            ll = row.get_level_labels()
            if name and ll:
                labels[name] = ll
        return labels

    def add_data_factor(self, factor_def: dict):
        """Add a single data-backed factor row."""
        row = self._create_factor_row(
            factor_def.get("name", ""),
            factor_def.get("n_levels", 2),
            factor_def.get("proportions", []),
        )
        level_labels = factor_def.get("level_labels")
        row.set_data_mode(level_labels=level_labels)
        self._factor_rows.append(row)
        self._factors_layout.addWidget(row)
        self._data_mode = True
        self._on_changed()

    def get_interactions(self) -> list[str]:
        """Return checked interaction terms (e.g. ['group1:group2'])."""
        if not self._interactions_check.isChecked():
            return []
        return [term for term, cb in self._interaction_checkboxes if cb.isChecked()]

    def get_dep_var(self) -> str:
        return "y"

    def set_dep_var(self, name: str):
        pass  # dep_var is always "y"

    def set_factors(self, factors: list[dict], interactions: list[str]):
        """Restore from history."""
        self._suppress_signals = True
        try:
            # Clear existing rows
            self._clear_factor_rows()
            for fdef in factors:
                row = self._create_factor_row(
                    fdef.get("name", ""),
                    fdef.get("n_levels", 2),
                    fdef.get("proportions", []),
                )
                self._factor_rows.append(row)
                self._factors_layout.addWidget(row)

            # Restore interactions
            if interactions:
                self._interactions_check.setChecked(True)
                self._rebuild_interaction_checkboxes()
                interaction_set = set(interactions)
                for term, cb in self._interaction_checkboxes:
                    cb.setChecked(term in interaction_set)
            else:
                self._interactions_check.setChecked(False)
        finally:
            self._suppress_signals = False
        self._on_changed()

    def set_data_factors(self, factors: list[dict]):
        """Populate factors from uploaded data and lock them."""
        self._suppress_signals = True
        try:
            self._clear_factor_rows()
            for fdef in factors:
                row = self._create_factor_row(
                    fdef.get("name", ""),
                    fdef.get("n_levels", 2),
                    fdef.get("proportions", []),
                )
                level_labels = fdef.get("level_labels")
                row.set_data_mode(level_labels=level_labels)
                self._factor_rows.append(row)
                self._factors_layout.addWidget(row)
            self._data_mode = True
        finally:
            self._suppress_signals = False
        self._on_changed()

    def clear_data_mode(self):
        """Unlock all rows from data mode."""
        if not self._data_mode:
            return
        self._data_mode = False
        for row in self._factor_rows:
            row.clear_data_mode()

    def get_factor_names(self) -> set[str]:
        """Return set of current factor names."""
        return {r.get_name() for r in self._factor_rows if r.get_name()}

    def clear_factors(self):
        """Remove all factor rows."""
        self._clear_factor_rows()

    def notify_changed(self):
        """Trigger formula/types rebuild and signal emission."""
        self._on_changed()

    def refresh(self):
        """Force a rebuild of the formula and re-emit all signals."""
        self._on_changed()

    # ── Internal ──────────────────────────────────────────────

    def _add_factor(self):
        """Add a new factor row with auto-generated name."""
        idx = len(self._factor_rows) + 1
        name = f"factor{idx}"
        # Ensure unique name
        existing_names = {r.get_name() for r in self._factor_rows}
        while name in existing_names:
            idx += 1
            name = f"factor{idx}"
        row = self._create_factor_row(name, 2, [])
        self._factor_rows.append(row)
        self._factors_layout.addWidget(row)
        self._on_changed()

    def _create_factor_row(
        self, name: str, n_levels: int, proportions: list[float]
    ) -> _FactorRow:
        row = _FactorRow(name, n_levels, proportions)
        row.changed.connect(self._on_changed)
        row.remove_requested.connect(lambda r=row: self._remove_factor(r))
        return row

    def _remove_factor(self, row: _FactorRow):
        if row in self._factor_rows:
            self._factor_rows.remove(row)
            self._factors_layout.removeWidget(row)
            row.deleteLater()
            # If no data-mode rows remain, exit data mode
            if self._data_mode and not any(r.is_data_mode() for r in self._factor_rows):
                self._data_mode = False
            self._on_changed()

    def _clear_factor_rows(self):
        for row in self._factor_rows:
            self._factors_layout.removeWidget(row)
            row.deleteLater()
        self._factor_rows.clear()

    def _on_interactions_toggled(self, checked: bool):
        if checked and len(self._factor_rows) >= 2:
            self._rebuild_interaction_checkboxes()
            self._interactions_container.show()
        else:
            self._interactions_container.hide()
        self._on_changed()

    def _rebuild_interaction_checkboxes(self):
        """Build checkboxes for all factor-pair interactions."""
        # Clear existing
        while self._interactions_layout.count():
            item = self._interactions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._interaction_checkboxes.clear()

        names = [r.get_name() for r in self._factor_rows if r.get_name()]
        if len(names) < 2:
            return

        for a, b in combinations(names, 2):
            term = f"{a}:{b}"
            cb = QCheckBox(f"{a} : {b}")
            cb.toggled.connect(lambda _: self._on_changed())
            self._interaction_checkboxes.append((term, cb))
            self._interactions_layout.addWidget(cb)

    def _on_changed(self):
        """Rebuild formula and emit signals."""
        if self._suppress_signals:
            return

        factor_names = [r.get_name() for r in self._factor_rows if r.get_name()]

        # Only rebuild interaction checkboxes when factor names actually change
        if self._interactions_check.isChecked():
            if factor_names != self._last_factor_names:
                old_checked = {
                    term for term, cb in self._interaction_checkboxes if cb.isChecked()
                }
                self._suppress_signals = True
                try:
                    self._rebuild_interaction_checkboxes()
                    for term, cb in self._interaction_checkboxes:
                        if term in old_checked:
                            cb.setChecked(True)
                finally:
                    self._suppress_signals = False
            if len(self._factor_rows) >= 2:
                self._interactions_container.show()
            else:
                self._interactions_container.hide()

        self._last_factor_names = list(factor_names)

        dep_var = self.get_dep_var()
        interactions = self.get_interactions()

        if not factor_names:
            self.formula_changed.emit("", dep_var, [])
            self.types_changed.emit({})
            return

        # Build formula
        terms = list(factor_names) + interactions
        formula = f"{dep_var} = {' + '.join(terms)}"

        # Build predictors list (factors + interaction terms)
        predictors = list(terms)

        self.formula_changed.emit(formula, dep_var, predictors)
        self.types_changed.emit(self.get_types())


class _FactorRow(QWidget):
    """Single factor row: [name] [levels spin] [proportions...] [normalize] [X]."""

    changed = Signal()
    remove_requested = Signal()

    def __init__(
        self,
        name: str = "",
        n_levels: int = 2,
        proportions: list[float] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._proportion_spins: list[QDoubleSpinBox] = []
        self._suppress = False
        self._data_mode = False
        self._level_labels: list[str] | None = None
        self._ref_combo: QComboBox | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)

        # Top row: name, levels, remove
        top = QHBoxLayout()

        self._name_edit = QLineEdit(name)
        self._name_edit.setFixedWidth(120)
        self._name_edit.setPlaceholderText("factor name")
        self._name_edit.textChanged.connect(lambda: self.changed.emit())
        top.addWidget(QLabel("Name:"))
        top.addWidget(self._name_edit)

        top.addWidget(QLabel("Levels:"))
        self._levels_spin = SpinBox()
        self._levels_spin.setRange(2, 20)
        self._levels_spin.setValue(n_levels)
        self._levels_spin.setFixedWidth(60)
        self._levels_spin.valueChanged.connect(self._on_levels_changed)
        top.addWidget(self._levels_spin)

        self._btn_remove = QPushButton("X")
        self._btn_remove.setFixedWidth(28)
        self._btn_remove.setToolTip("Remove this factor")
        self._btn_remove.clicked.connect(self.remove_requested.emit)
        top.addWidget(self._btn_remove)

        top.addStretch()
        outer.addLayout(top)

        # Proportions row
        self._prop_container = QWidget()
        self._prop_layout = QHBoxLayout(self._prop_container)
        self._prop_layout.setContentsMargins(20, 0, 0, 0)
        outer.addWidget(self._prop_container)

        self._build_proportions(n_levels, proportions or [])

    def set_data_mode(self, level_labels: list[str] | None = None):
        """Lock this row for data-upload mode."""
        self._data_mode = True
        self._name_edit.setReadOnly(True)
        self._name_edit.setFrame(False)
        self._name_edit.setStyleSheet("background: transparent;")
        self._levels_spin.setEnabled(False)
        self._prop_container.hide()
        if level_labels:
            self._level_labels = level_labels
            self._build_reference_selector(level_labels)

    def clear_data_mode(self):
        """Unlock this row from data-upload mode."""
        if not self._data_mode:
            return
        self._data_mode = False
        self._name_edit.setReadOnly(False)
        self._name_edit.setFrame(True)
        self._name_edit.setStyleSheet("")
        self._levels_spin.setEnabled(True)
        self._prop_container.show()

    def _build_reference_selector(self, labels: list[str]):
        """Add a combo box to pick the reference level."""
        ref_row = QWidget()
        ref_layout = QHBoxLayout(ref_row)
        ref_layout.setContentsMargins(20, 0, 0, 0)
        ref_layout.addWidget(QLabel("Reference:"))
        self._ref_combo = QComboBox()
        self._ref_combo.addItems(labels)
        self._ref_combo.setCurrentIndex(0)  # First sorted value is default reference
        self._ref_combo.setFixedWidth(120)
        self._ref_combo.currentTextChanged.connect(lambda: self.changed.emit())
        ref_layout.addWidget(self._ref_combo)
        ref_layout.addWidget(QLabel(f"Levels: {', '.join(labels)}"))
        ref_layout.addStretch()

        # Add to the outer layout (after the top row)
        self.layout().addWidget(ref_row)

    def get_reference_level(self) -> str | None:
        """Return the selected reference level, or None if not in data mode."""
        if self._ref_combo is not None:
            return self._ref_combo.currentText()
        return None

    def get_level_labels(self) -> list[str] | None:
        return self._level_labels

    def is_data_mode(self) -> bool:
        return self._data_mode

    def get_name(self) -> str:
        return self._name_edit.text().strip()

    def get_n_levels(self) -> int:
        return self._levels_spin.value()

    def get_proportions(self) -> list[float]:
        return [s.value() for s in self._proportion_spins]

    def _on_levels_changed(self, n_levels: int):
        self._build_proportions(n_levels, [])
        self.changed.emit()

    def _build_proportions(self, n_levels: int, existing: list[float]):
        """Create proportion spinboxes for each level."""
        while self._prop_layout.count():
            item = self._prop_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._proportion_spins = []

        if len(existing) == n_levels:
            props = list(existing)
        else:
            props = [round(1.0 / n_levels, 4)] * n_levels

        self._prop_layout.addWidget(QLabel("Proportions:"))
        for i in range(n_levels):
            spin = DoubleSpinBox()
            spin.setRange(0.01, 0.99)
            spin.setSingleStep(0.05)
            spin.setDecimals(2)
            spin.setValue(props[i] if i < len(props) else round(1.0 / n_levels, 4))
            spin.setFixedWidth(60)
            spin.setToolTip(f"Level {i + 1}")
            spin.valueChanged.connect(self._on_proportion_changed)
            self._prop_layout.addWidget(spin)
            self._proportion_spins.append(spin)

        normalize_btn = QPushButton("(to 100%)")
        normalize_btn.setFixedWidth(80)
        normalize_btn.setToolTip("Normalize proportions to sum to 1.0")
        normalize_btn.clicked.connect(self._normalize)
        self._prop_layout.addWidget(normalize_btn)
        self._prop_layout.addStretch()

    def _on_proportion_changed(self):
        if not self._suppress:
            self.changed.emit()

    def _normalize(self):
        self._suppress = True
        try:
            raw = [s.value() for s in self._proportion_spins]
            total = sum(raw)
            if total > 0:
                normalized = [round(v / total, 2) for v in raw]
                diff = round(1.0 - sum(normalized), 2)
                normalized[-1] = round(normalized[-1] + diff, 2)
                for spin, val in zip(self._proportion_spins, normalized):
                    spin.setValue(val)
        finally:
            self._suppress = False
        self.changed.emit()
