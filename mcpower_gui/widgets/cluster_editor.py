"""Dynamic cluster configuration editor for mixed model random effects."""

from __future__ import annotations

__all__ = ["ClusterEditor"]

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui.widgets.spin_boxes import DoubleSpinBox, SpinBox


class ClusterEditor(QWidget):
    """Dynamically renders config cards per random effect term.

    Call ``set_random_effects()`` with the parsed random effects list from
    FormulaInput. Emits ``clusters_changed(list)`` when any parameter changes.
    """

    clusters_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: list[_ClusterCard] = []
        self._prev_configs: dict[str, dict] = {}  # grouping_var -> last config

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def set_random_effects(self, random_effects: list[dict], predictors: list[str]):
        """Rebuild cards from parsed random effects.

        Preserves user-edited values for random effects that still exist.
        """
        # Save current values before rebuilding
        for card in self._cards:
            cfg = card.get_config()
            self._prev_configs[cfg["grouping_var"]] = cfg

        # Clear old cards
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        # Build new cards
        for re_info in random_effects:
            prev = self._prev_configs.get(re_info["grouping_var"], {})
            card = _ClusterCard(re_info, prev)
            card.changed.connect(self._emit)
            self._cards.append(card)
            self._layout.addWidget(card)

        self._emit()

    def get_cluster_configs(self) -> list[dict]:
        """Return list of cluster config dicts."""
        return [card.get_config() for card in self._cards]

    def clear(self):
        """Remove all cards."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()
        self._prev_configs.clear()

    def _emit(self):
        self.clusters_changed.emit(self.get_cluster_configs())


class _ClusterCard(QGroupBox):
    """Configuration card for a single random effect term."""

    changed = Signal()

    def __init__(self, re_info: dict, prev: dict, parent=None):
        self._re_info = re_info
        gv = re_info["grouping_var"]
        is_nested_child = bool(re_info.get("parent_var"))
        is_slope = re_info["type"] == "random_slope"

        # Title
        if is_slope:
            slopes = ", ".join(re_info.get("slope_vars", []))
            title = f"{gv} (random slope: {slopes})"
        elif is_nested_child:
            parent_var = re_info["parent_var"]
            child_name = gv.split(":")[-1] if ":" in gv else gv
            title = f"{child_name} (nested in {parent_var})"
        else:
            title = f"{gv} (random intercept)"

        super().__init__(title, parent)
        form = QFormLayout(self)

        # ICC (always present)
        self._icc_spin = DoubleSpinBox()
        self._icc_spin.setRange(0.0, 0.99)
        self._icc_spin.setSingleStep(0.05)
        self._icc_spin.setDecimals(2)
        self._icc_spin.setValue(prev.get("ICC", 0.2))
        self._icc_spin.valueChanged.connect(lambda: self.changed.emit())
        form.addRow("ICC:", self._icc_spin)

        # N clusters or N per parent
        self._n_clusters_spin = None
        self._n_per_parent_spin = None

        if is_nested_child:
            self._n_per_parent_spin = SpinBox()
            self._n_per_parent_spin.setRange(2, 1000)
            self._n_per_parent_spin.setValue(prev.get("n_per_parent", 3))
            self._n_per_parent_spin.valueChanged.connect(lambda: self.changed.emit())
            form.addRow("N per parent:", self._n_per_parent_spin)
        else:
            self._n_clusters_spin = SpinBox()
            self._n_clusters_spin.setRange(2, 10000)
            self._n_clusters_spin.setValue(prev.get("n_clusters", 20))
            self._n_clusters_spin.valueChanged.connect(lambda: self.changed.emit())
            form.addRow("N clusters:", self._n_clusters_spin)

        # Slope parameters (only for random_slope)
        self._slope_variance_spin = None
        self._slope_intercept_corr_spin = None

        if is_slope:
            self._slope_variance_spin = DoubleSpinBox()
            self._slope_variance_spin.setRange(0.0, 10.0)
            self._slope_variance_spin.setSingleStep(0.05)
            self._slope_variance_spin.setDecimals(2)
            self._slope_variance_spin.setValue(prev.get("slope_variance", 0.1))
            self._slope_variance_spin.valueChanged.connect(lambda: self.changed.emit())
            form.addRow("Slope variance:", self._slope_variance_spin)

            self._slope_intercept_corr_spin = DoubleSpinBox()
            self._slope_intercept_corr_spin.setRange(-1.0, 1.0)
            self._slope_intercept_corr_spin.setSingleStep(0.1)
            self._slope_intercept_corr_spin.setDecimals(2)
            self._slope_intercept_corr_spin.setValue(
                prev.get("slope_intercept_corr", 0.0)
            )
            self._slope_intercept_corr_spin.valueChanged.connect(
                lambda: self.changed.emit()
            )
            form.addRow("Slope-intercept corr:", self._slope_intercept_corr_spin)

    def get_config(self) -> dict:
        """Return config dict for this random effect."""
        cfg: dict = {
            "grouping_var": self._re_info["grouping_var"],
            "ICC": self._icc_spin.value(),
        }

        if self._re_info.get("parent_var"):
            cfg["parent_var"] = self._re_info["parent_var"]

        if self._n_clusters_spin is not None:
            cfg["n_clusters"] = self._n_clusters_spin.value()
        if self._n_per_parent_spin is not None:
            cfg["n_per_parent"] = self._n_per_parent_spin.value()

        if self._re_info["type"] == "random_slope":
            cfg["random_slopes"] = list(self._re_info.get("slope_vars", []))
            if self._slope_variance_spin is not None:
                cfg["slope_variance"] = self._slope_variance_spin.value()
            if self._slope_intercept_corr_spin is not None:
                cfg["slope_intercept_corr"] = self._slope_intercept_corr_spin.value()

        return cfg
