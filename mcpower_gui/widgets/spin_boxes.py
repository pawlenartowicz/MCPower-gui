"""Block wheel-scroll from changing any input widget's value.

Scrolling the mouse wheel over a spin box or combo box should scroll the
page, not change the widget's value.  Two layers enforce this:

1.  ``WheelGuard`` — an **application-level** event filter installed on
    ``QApplication``.  It intercepts *every* event Qt delivers.  When the
    target is a ``QAbstractSpinBox`` or ``QComboBox``, it eats the wheel
    event and programmatically scrolls the nearest ancestor
    ``QScrollArea`` instead.

2.  ``SpinBox`` / ``DoubleSpinBox`` subclasses that override
    ``wheelEvent`` to unconditionally ignore wheel input (defence in
    depth in case something bypasses the global filter).
"""

__all__ = ["WheelGuard", "SpinBox", "DoubleSpinBox", "install_wheel_guard"]

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QDoubleSpinBox,
    QScrollArea,
    QSpinBox,
    QWidget,
)

# Widget types that must never react to the mouse wheel.
_GUARDED = (QAbstractSpinBox, QComboBox)


# ---------------------------------------------------------------------------
# Application-level event filter
# ---------------------------------------------------------------------------


class WheelGuard(QObject):
    """Blocks wheel events on input widgets and scrolls the page instead."""

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() != QEvent.Type.Wheel:
            return False

        if not isinstance(obj, _GUARDED):
            return False

        # --- Scroll the nearest ancestor QScrollArea instead -------------
        wheel: QWheelEvent = event  # type: ignore[assignment]
        scroll_area = _find_scroll_area(obj)
        if scroll_area is not None:
            sb = scroll_area.verticalScrollBar()
            pixels = wheel.pixelDelta().y()
            if pixels != 0:
                sb.setValue(sb.value() - pixels)
            else:
                step = sb.singleStep() * 3
                notches = wheel.angleDelta().y() / 120.0
                sb.setValue(sb.value() - int(notches * step))

        return True  # always block delivery to the input widget


def _find_scroll_area(widget: QWidget) -> QScrollArea | None:
    parent = widget.parent()
    while parent is not None:
        if isinstance(parent, QScrollArea):
            return parent
        parent = parent.parent()
    return None


def install_wheel_guard(app: QObject) -> WheelGuard:
    """Install the global ``WheelGuard`` on *app* (must be ``QApplication``)."""
    guard = WheelGuard(app)
    app.installEventFilter(guard)
    return guard


# ---------------------------------------------------------------------------
# Spin-box subclasses (defence in depth)
# ---------------------------------------------------------------------------


class SpinBox(QSpinBox):
    """QSpinBox that never reacts to the mouse wheel."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        event.ignore()


class DoubleSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox that never reacts to the mouse wheel."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        event.ignore()
