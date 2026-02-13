"""Checklist widget for selecting target tests — Select All + per-test checkboxes."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

_ROW_HEIGHT = 26
_MAX_HEIGHT = 200
_PADDING = 8


class TargetTestSelector(QWidget):
    """Scrollable checklist with a Select All checkbox and one checkbox per test.

    All tests are checked by default. ``get_value()`` returns ``"all"`` when
    every test is selected, otherwise a comma-separated string of selected names.
    """

    selection_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checkboxes: list[tuple[str, QCheckBox]] = []
        self._suppress = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)

        self._select_all = QCheckBox("Select All")
        self._select_all.setChecked(True)
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

    def set_tests(self, tests: list[str]):
        """Rebuild checkboxes for *tests*. All checked by default."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._checkboxes.clear()

        for name in tests:
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_item_changed)
            self._layout.addWidget(cb)
            self._checkboxes.append((name, cb))

        self._suppress = True
        self._select_all.setCheckState(Qt.CheckState.Checked)
        self._suppress = False
        self._update_scroll_height()

    def get_value(self) -> str:
        """Return ``"all"`` if all checked, else comma-separated selected names."""
        selected = [name for name, cb in self._checkboxes if cb.isChecked()]
        if len(selected) == len(self._checkboxes):
            return "all"
        return ", ".join(selected)

    # ── Internal ─────────────────────────────────────────────

    def _on_select_all(self, state: int):
        if self._suppress:
            return
        self._suppress = True
        checked = state == Qt.CheckState.Checked.value
        for _, cb in self._checkboxes:
            cb.setChecked(checked)
        self._suppress = False
        self._emit()

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
        self._emit()

    def _emit(self):
        self.selection_changed.emit(self.get_value())

    def _update_scroll_height(self):
        n = len(self._checkboxes)
        h = min(n * _ROW_HEIGHT + _PADDING, _MAX_HEIGHT)
        self._scroll.setMinimumHeight(h)
        self._scroll.setMaximumHeight(h)
