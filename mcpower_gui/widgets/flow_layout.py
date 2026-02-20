"""Flow widget — arranges child buttons left-to-right, wrapping to the next row."""

from __future__ import annotations

__all__ = ["FlowWidget"]

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtWidgets import QSizePolicy, QWidget


class FlowWidget(QWidget):
    """A widget that arranges its child widgets left-to-right, wrapping
    to the next row when they exceed the available width.

    Add children directly as child widgets (parent=self). Call
    ``reflow()`` after adding/removing children.
    """

    def __init__(self, parent: QWidget | None = None, h_spacing: int = 6, v_spacing: int = 6):
        super().__init__(parent)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def reflow(self):
        """Reposition children and update fixed height."""
        width = self.width() if self.width() > 0 else 400
        h = self._layout_children(width)
        self.setFixedHeight(max(h, 0))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_children(event.size().width())

    def _layout_children(self, width: int) -> int:
        """Position children left-to-right with wrapping. Returns total height."""
        children = [
            c for c in self.findChildren(
                QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly
            )
            if c.isVisible()
        ]
        if not children:
            return 0

        x = 0
        y = 0
        row_height = 0

        for child in children:
            sz = child.sizeHint()
            if sz.isEmpty():
                sz = child.size()
            next_x = x + sz.width() + self._h_spacing
            if next_x - self._h_spacing > width and row_height > 0:
                x = 0
                y += row_height + self._v_spacing
                next_x = sz.width() + self._h_spacing
                row_height = 0
            child.move(QPoint(x, y))
            child.resize(sz)
            x = next_x
            row_height = max(row_height, sz.height())

        return y + row_height

    def sizeHint(self) -> QSize:
        width = self.width() if self.width() > 0 else 400
        h = self._layout_children_dry(width)
        return QSize(width, max(h, 0))

    def _layout_children_dry(self, width: int) -> int:
        """Calculate height without moving children."""
        children = [
            c for c in self.findChildren(
                QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly
            )
            if c.isVisible()
        ]
        if not children:
            return 0
        x = 0
        y = 0
        row_height = 0
        for child in children:
            sz = child.sizeHint()
            if sz.isEmpty():
                sz = child.size()
            next_x = x + sz.width() + self._h_spacing
            if next_x - self._h_spacing > width and row_height > 0:
                x = 0
                y += row_height + self._v_spacing
                next_x = sz.width() + self._h_spacing
                row_height = 0
            x = next_x
            row_height = max(row_height, sz.height())
        return y + row_height
