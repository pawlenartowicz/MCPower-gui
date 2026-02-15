"""Tests for the UpdateBanner widget."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

from mcpower_gui.widgets.update_banner import UpdateBanner


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
