"""Acknowledgments dialog — displays acknowledgments.txt in a read-only view."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui._resources import resource_path


def _load_acknowledgments_text() -> str:
    return resource_path("acknowledgments.txt").read_text(encoding="utf-8")


class AcknowledgmentsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Acknowledgments")
        self.resize(480, 340)

        root = QVBoxLayout(self)

        text = _load_acknowledgments_text()
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setStyleSheet("padding: 12px;")
        root.addWidget(label, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.close)
        root.addWidget(buttons)
