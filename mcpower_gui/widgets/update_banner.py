"""Dismissible info bar shown when a newer version is available."""

from __future__ import annotations

from PySide6.QtCore import QUrl, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from mcpower_gui.theme import current_mode, is_dark, ThemeMode

# Theme-specific banner styles: (bg, border, text, link)
_STYLES = {
    "light": ("#ddeeff", "#aaccee", "#1a1a1a", "#0066cc"),
    "dark": ("#1a3a4a", "#2a5a6a", "#dcdcdc", "#5caadd"),
    "dark_pink": ("#3a1a2a", "#6a2a4a", "#dcdcdc", "#f48fb1"),
}


def _style_key() -> str:
    if current_mode() == ThemeMode.DARK_PINK:
        return "dark_pink"
    return "dark" if is_dark() else "light"


class UpdateBanner(QFrame):
    """A horizontal banner: 'MCPower vX.Y.Z is available  [Download] [X]'."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self._label = QLabel()
        layout.addWidget(self._label, stretch=1)

        self._download_btn = QPushButton("Download")
        self._download_btn.setFlat(True)
        layout.addWidget(self._download_btn)

        self._dismiss_btn = QPushButton("\u2715")
        self._dismiss_btn.setFixedSize(24, 24)
        self._dismiss_btn.setFlat(True)
        layout.addWidget(self._dismiss_btn)

        self._dismiss_btn.clicked.connect(self.hide)

        self._release_url = ""
        self._download_btn.clicked.connect(self._open_release)

        self._apply_theme_style()
        self.hide()

        app = QApplication.instance()
        if app is not None:
            app.paletteChanged.connect(self._apply_theme_style)

    def _apply_theme_style(self) -> None:
        bg, border, text, link = _STYLES[_style_key()]
        self.setStyleSheet(
            f"UpdateBanner {{"
            f"  background-color: {bg};"
            f"  border: 1px solid {border};"
            f"  border-radius: 4px;"
            f"  padding: 4px 8px;"
            f"  color: {text};"
            f"}}"
        )
        self._label.setStyleSheet(f"color: {text};")
        self._download_btn.setStyleSheet(f"color: {link}; text-decoration: underline;")

    @Slot(str, str)
    def show_update(self, version: str, release_url: str) -> None:
        self._label.setText(f"MCPower v{version} is available")
        self._release_url = release_url
        self.show()

    def _open_release(self) -> None:
        if self._release_url:
            QDesktopServices.openUrl(QUrl(self._release_url))
