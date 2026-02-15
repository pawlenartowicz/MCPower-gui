"""Tests for the theme module."""

import os
import sys

import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# Ensure a QApplication exists before importing theme
_app = QApplication.instance() or QApplication(sys.argv)

from mcpower_gui import theme
from mcpower_gui.theme import (
    ThemeMode,
    apply_theme,
    current_colors,
    current_mode,
    is_dark,
    save_theme_mode,
    saved_theme_mode,
)


@pytest.fixture(autouse=True)
def _reset_theme():
    """Reset to light after each test to avoid cross-contamination."""
    yield
    apply_theme(ThemeMode.LIGHT)


class TestThemeMode:
    def test_enum_values(self):
        assert ThemeMode.SYSTEM.value == "system"
        assert ThemeMode.LIGHT.value == "light"
        assert ThemeMode.DARK.value == "dark"
        assert ThemeMode.DARK_PINK.value == "dark_pink"


class TestApplyTheme:
    def test_light_sets_light_palette(self):
        apply_theme(ThemeMode.LIGHT)
        assert not is_dark()
        palette = _app.palette()
        # Light theme has white base
        assert palette.color(QPalette.ColorRole.Base) == QColor(255, 255, 255)

    def test_dark_sets_dark_palette(self):
        apply_theme(ThemeMode.DARK)
        assert is_dark()
        palette = _app.palette()
        # Dark theme has dark base
        assert palette.color(QPalette.ColorRole.Base) == QColor(35, 35, 35)

    def test_sets_fusion_style(self):
        apply_theme(ThemeMode.LIGHT)
        assert _app.style().name().lower() == "fusion"

    def test_loads_from_settings_when_no_mode(self):
        save_theme_mode(ThemeMode.DARK)
        apply_theme()  # no argument — should read from settings
        assert is_dark()


class TestCurrentColors:
    def test_light_colors(self):
        apply_theme(ThemeMode.LIGHT)
        colors = current_colors()
        assert colors["plot_bg"] == "#ffffff"
        assert colors["plot_fg"] == "#000000"
        assert "muted" in colors
        assert "success" in colors
        assert "error" in colors
        assert "script_bg" in colors
        assert "script_fg" in colors
        assert "border" in colors

    def test_dark_colors(self):
        apply_theme(ThemeMode.DARK)
        colors = current_colors()
        assert colors["plot_bg"] == "#232323"
        assert colors["plot_fg"] == "#dcdcdc"

    def test_colors_change_with_theme(self):
        apply_theme(ThemeMode.LIGHT)
        light_bg = current_colors()["plot_bg"]
        apply_theme(ThemeMode.DARK)
        dark_bg = current_colors()["plot_bg"]
        assert light_bg != dark_bg


class TestPersistence:
    def test_save_and_load(self):
        save_theme_mode(ThemeMode.DARK)
        assert saved_theme_mode() == ThemeMode.DARK
        save_theme_mode(ThemeMode.LIGHT)
        assert saved_theme_mode() == ThemeMode.LIGHT
        save_theme_mode(ThemeMode.SYSTEM)
        assert saved_theme_mode() == ThemeMode.SYSTEM

    def test_invalid_value_falls_back_to_system(self):
        from PySide6.QtCore import QSettings

        settings = QSettings("MCPower", "MCPower")
        settings.setValue("theme", "garbage")
        assert saved_theme_mode() == ThemeMode.SYSTEM


class TestDarkPalette:
    def test_disabled_text_is_dimmer(self):
        apply_theme(ThemeMode.DARK)
        palette = _app.palette()
        normal = palette.color(QPalette.ColorGroup.Normal, QPalette.ColorRole.Text)
        disabled = palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text)
        # Disabled text should be dimmer (lower luminance)
        assert disabled.lightness() < normal.lightness()


class TestDarkPinkTheme:
    def test_dark_pink_is_dark(self):
        apply_theme(ThemeMode.DARK_PINK)
        assert is_dark()

    def test_dark_pink_has_pink_highlight(self):
        apply_theme(ThemeMode.DARK_PINK)
        palette = _app.palette()
        highlight = palette.color(QPalette.ColorRole.Highlight)
        assert highlight == QColor("#e91e63")

    def test_dark_pink_has_pink_link(self):
        apply_theme(ThemeMode.DARK_PINK)
        palette = _app.palette()
        link = palette.color(QPalette.ColorRole.Link)
        assert link == QColor("#f48fb1")

    def test_dark_pink_has_pink_bright_text(self):
        apply_theme(ThemeMode.DARK_PINK)
        palette = _app.palette()
        bright = palette.color(QPalette.ColorRole.BrightText)
        assert bright == QColor("#ff80ab")

    def test_dark_pink_same_base_as_dark(self):
        apply_theme(ThemeMode.DARK_PINK)
        dp_base = _app.palette().color(QPalette.ColorRole.Base)
        apply_theme(ThemeMode.DARK)
        dark_base = _app.palette().color(QPalette.ColorRole.Base)
        assert dp_base == dark_base

    def test_dark_pink_colors_same_as_dark(self):
        apply_theme(ThemeMode.DARK_PINK)
        dp_colors = current_colors()
        apply_theme(ThemeMode.DARK)
        dark_colors = current_colors()
        assert dp_colors == dark_colors

    def test_current_mode_tracks_dark_pink(self):
        apply_theme(ThemeMode.DARK_PINK)
        assert current_mode() == ThemeMode.DARK_PINK

    def test_current_mode_tracks_light(self):
        apply_theme(ThemeMode.LIGHT)
        assert current_mode() == ThemeMode.LIGHT

    def test_persistence_dark_pink(self):
        save_theme_mode(ThemeMode.DARK_PINK)
        assert saved_theme_mode() == ThemeMode.DARK_PINK
