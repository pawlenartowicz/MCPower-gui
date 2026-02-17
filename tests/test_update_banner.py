"""Tests for the UpdateBanner widget."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

from mcpower_gui.theme import ThemeMode, apply_theme  # noqa: E402
from mcpower_gui.widgets.update_banner import UpdateBanner  # noqa: E402


class TestUpdateBanner:
    def test_hidden_by_default(self):
        banner = UpdateBanner()
        assert not banner.isVisible()

    def test_show_update_makes_visible(self):
        banner = UpdateBanner()
        banner.show_update("1.0.0", "https://example.com/release")
        assert banner.isVisible()

    def test_dismiss_hides(self):
        banner = UpdateBanner()
        banner.show_update("1.0.0", "https://example.com/release")
        banner._dismiss_btn.click()
        assert not banner.isVisible()

    def test_label_contains_version(self):
        banner = UpdateBanner()
        banner.show_update("2.0.0", "https://example.com/release")
        assert "2.0.0" in banner._label.text()

    def test_style_updates_on_theme_change(self):
        apply_theme(ThemeMode.LIGHT)
        banner = UpdateBanner()
        light_style = banner.styleSheet()
        apply_theme(ThemeMode.DARK)
        dark_style = banner.styleSheet()
        assert light_style != dark_style
        assert "#1a3a4a" in dark_style  # dark bg color
        apply_theme(ThemeMode.LIGHT)

    def test_dark_pink_uses_pink_style(self):
        apply_theme(ThemeMode.DARK_PINK)
        banner = UpdateBanner()
        style = banner.styleSheet()
        assert "#3a1a2a" in style  # dark pink bg color
        link_style = banner._download_btn.styleSheet()
        assert "#f48fb1" in link_style  # pink link color
        apply_theme(ThemeMode.LIGHT)
