"""Dismissible info bar shown when a newer version is available."""

from __future__ import annotations

from PySide6.QtCore import QUrl, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
)


class UpdateBanner(QFrame):
    """A horizontal banner: 'MCPower vX.Y.Z is available  [Download] [X]'."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "UpdateBanner {"
            "  background-color: #ddeeff;"
            "  border: 1px solid #aaccee;"
            "  border-radius: 4px;"
            "  padding: 4px 8px;"
            "}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self._label = QLabel()
        layout.addWidget(self._label, stretch=1)

        self._download_btn = QPushButton("Download")
        self._download_btn.setFlat(True)
        self._download_btn.setStyleSheet("color: #0066cc; text-decoration: underline;")
        layout.addWidget(self._download_btn)

        self._dismiss_btn = QPushButton("\u2715")
        self._dismiss_btn.setFixedSize(24, 24)
        self._dismiss_btn.setFlat(True)
        layout.addWidget(self._dismiss_btn)

        self._dismiss_btn.clicked.connect(self.hide)

        self._release_url = ""
        self._download_btn.clicked.connect(self._open_release)

        self.hide()

    @Slot(str, str)
    def show_update(self, version: str, release_url: str) -> None:
        self._label.setText(f"MCPower v{version} is available")
        self._release_url = release_url
        self.show()

    def _open_release(self) -> None:
        if self._release_url:
            QDesktopServices.openUrl(QUrl(self._release_url))
