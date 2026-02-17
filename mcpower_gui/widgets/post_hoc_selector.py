"""Checkbox widget for selecting post hoc pairwise comparisons."""

from itertools import combinations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

_ROW_HEIGHT = 26
_MAX_HEIGHT = 200
_PADDING = 8


class PostHocSelector(QWidget):
    """Scrollable checklist of pairwise comparisons auto-generated from factors.

    All comparisons are **unchecked** by default — post hoc tests must be
    explicitly opted into.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checkboxes: list[tuple[str, QCheckBox]] = []
        self._suppress = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)

        self._select_all = QCheckBox("Select All")
        self._select_all.setChecked(False)
        self._select_all.setTristate(True)
        self._select_all.stateChanged.connect(self._on_select_all)
        outer.addWidget(self._select_all)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._layout.setContentsMargins(16, 0, 0, 0)
        self._layout.setSpacing(2)
        self._scroll.setWidget(self._container)
        outer.addWidget(self._scroll)

    # ── Public API ───────────────────────────────────────────

    def set_factors(self, factors: dict[str, int]) -> None:
        """Rebuild comparison checkboxes from ``{factor_name: n_levels}``.

        Generates all pairwise comparisons using 1-indexed levels.
        For factor "group" with 3 levels: group[1] vs group[2],
        group[1] vs group[3], group[2] vs group[3].
        """
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._checkboxes.clear()

        for factor_name, n_levels in sorted(factors.items()):
            if n_levels < 2:
                continue
            # Section label for multi-factor models
            if len(factors) > 1:
                label = QLabel(f"{factor_name}:")
                label.setStyleSheet("font-weight: bold; margin-top: 4px;")
                self._layout.addWidget(label)

            for a, b in combinations(range(1, n_levels + 1), 2):
                comparison = f"{factor_name}[{a}] vs {factor_name}[{b}]"
                cb = QCheckBox(comparison)
                cb.setChecked(False)
                cb.stateChanged.connect(self._on_item_changed)
                self._layout.addWidget(cb)
                self._checkboxes.append((comparison, cb))

        self._suppress = True
        self._select_all.setCheckState(Qt.CheckState.Unchecked)
        self._suppress = False
        self._update_scroll_height()

    def get_selected(self) -> list[str]:
        """Return list of selected comparison strings."""
        return [name for name, cb in self._checkboxes if cb.isChecked()]

    def has_any_factors(self) -> bool:
        """Return True if any comparisons are available."""
        return len(self._checkboxes) > 0

    # ── Internal ─────────────────────────────────────────────

    def _on_select_all(self, state: int):
        if self._suppress:
            return
        self._suppress = True
        checked = state == Qt.CheckState.Checked.value
        for _, cb in self._checkboxes:
            cb.setChecked(checked)
        self._suppress = False

    def _on_item_changed(self):
        if self._suppress:
            return
        self._suppress = True
        checked_count = sum(1 for _, cb in self._checkboxes if cb.isChecked())
        total = len(self._checkboxes)
        if checked_count == total:
            self._select_all.setCheckState(Qt.CheckState.Checked)
        elif checked_count == 0:
            self._select_all.setCheckState(Qt.CheckState.Unchecked)
        else:
            self._select_all.setCheckState(Qt.CheckState.PartiallyChecked)
        self._suppress = False

    def _update_scroll_height(self):
        n = len(self._checkboxes)
        # Account for section labels in multi-factor cases
        h = min(n * _ROW_HEIGHT + _PADDING, _MAX_HEIGHT)
        self._scroll.setMinimumHeight(max(h, _ROW_HEIGHT))
        self._scroll.setMaximumHeight(max(h, _MAX_HEIGHT) if n > 0 else _ROW_HEIGHT)
