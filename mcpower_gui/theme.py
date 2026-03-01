"""Light / dark theme support using Fusion style + QPalette."""

from enum import Enum

from PySide6.QtCore import QRectF, QSettings, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPalette, QPen
from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle


class ThemeMode(Enum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"
    DARK_PINK = "dark_pink"


_SETTINGS_KEY = "theme"
_FONT_SIZE_KEY = "font_size"

# Current resolved dark/light state (set by apply_theme)
_is_dark: bool = False
_current_mode: ThemeMode = ThemeMode.SYSTEM
_current_style: "CardProxyStyle | None" = None


# ---------------------------------------------------------------------------
# Card proxy style — replaces only PE_FrameGroupBox painting
# ---------------------------------------------------------------------------


class CardProxyStyle(QProxyStyle):
    """Fusion-based style that draws QGroupBox frames as rounded cards."""

    def __init__(self, card_bg: str, card_border: str):
        super().__init__("Fusion")
        self._card_bg = QColor(card_bg)
        self._card_border = QColor(card_border)

    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PrimitiveElement.PE_FrameGroupBox:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = QRectF(option.rect).adjusted(0.5, 0.5, -0.5, -0.5)
            path = QPainterPath()
            path.addRoundedRect(rect, 6, 6)
            painter.fillPath(path, self._card_bg)
            painter.setPen(QPen(self._card_border, 1.0))
            painter.drawPath(path)
            painter.restore()
            return
        super().drawPrimitive(element, option, painter, widget)


# ---------------------------------------------------------------------------
# Tab-only QSS (no QGroupBox rules — proxy style handles those)
# ---------------------------------------------------------------------------


def _generate_stylesheet(mode: ThemeMode, dark: bool) -> str:
    """Return a global QSS string for tab styling only."""
    if mode == ThemeMode.DARK_PINK:
        tab_bg = "#3a3035"
        tab_selected_bg = "#4a3845"
        tab_border = "#5a3a4a"
        tab_accent = "#e91e63"
        tab_text = "#dcdcdc"
        tab_muted = "#aa7891"
    elif dark:
        tab_bg = "#353535"
        tab_selected_bg = "#444444"
        tab_border = "#5a5a5a"
        tab_accent = "#2a82da"
        tab_text = "#dcdcdc"
        tab_muted = "#999999"
    else:
        tab_bg = "#e8e8e8"
        tab_selected_bg = "#ffffff"
        tab_border = "#c8c8c8"
        tab_accent = "#2a82da"
        tab_text = "#000000"
        tab_muted = "#666666"

    return f"""
        QTabWidget::pane {{
            border: 1px solid {tab_border};
            top: -1px;
        }}
        QTabBar::tab {{
            background: {tab_bg};
            color: {tab_muted};
            border: 1px solid {tab_border};
            border-bottom: none;
            padding: 8px 20px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        QTabBar::tab:selected {{
            background: {tab_selected_bg};
            color: {tab_text};
            font-weight: bold;
            border-bottom: 2px solid {tab_accent};
        }}
        QTabBar::tab:hover:!selected {{
            background: {tab_selected_bg};
            color: {tab_text};
        }}
    """


# ---------------------------------------------------------------------------
# Palette builders
# ---------------------------------------------------------------------------


def _detect_system_dark() -> bool:
    """Return True if the OS is in dark mode."""
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        return False
    hints = app.styleHints()
    if hints is None:
        return False
    scheme = hints.colorScheme()
    return scheme == Qt.ColorScheme.Dark


def _build_light_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    p.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    p.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    p.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    p.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    p.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    p.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    p.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(128, 128, 128))
    p.setColor(QPalette.ColorRole.Mid, QColor(200, 200, 200))
    return p


def _build_dark_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    p.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.BrightText, QColor(255, 50, 50))
    p.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    p.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(140, 140, 140))
    p.setColor(QPalette.ColorRole.Mid, QColor(80, 80, 80))
    # Disabled state
    p.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor(120, 120, 120),
    )
    p.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(120, 120, 120)
    )
    p.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor(120, 120, 120),
    )
    return p


def _build_dark_pink_palette() -> QPalette:
    """Dark palette with pink accents throughout."""
    p = _build_dark_palette()
    # Core pink accents
    p.setColor(QPalette.ColorRole.Highlight, QColor("#e91e63"))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    p.setColor(QPalette.ColorRole.Link, QColor("#f48fb1"))
    p.setColor(QPalette.ColorRole.BrightText, QColor("#ff80ab"))
    # Subtle pink tint on surfaces
    p.setColor(QPalette.ColorRole.Window, QColor(58, 48, 53))
    p.setColor(QPalette.ColorRole.Base, QColor(40, 32, 36))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(50, 40, 45))
    p.setColor(QPalette.ColorRole.Button, QColor(58, 48, 53))
    # Pink-tinted mid / placeholder
    p.setColor(QPalette.ColorRole.Mid, QColor(100, 70, 85))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(170, 120, 145))
    return p


# ---------------------------------------------------------------------------
# Settings persistence
# ---------------------------------------------------------------------------


def saved_theme_mode() -> ThemeMode:
    """Read persisted theme preference from QSettings."""
    settings = QSettings("MCPower", "MCPower")
    value = settings.value(_SETTINGS_KEY, "system")
    try:
        return ThemeMode(value)
    except ValueError:
        return ThemeMode.SYSTEM


def save_theme_mode(mode: ThemeMode) -> None:
    """Persist theme preference to QSettings."""
    settings = QSettings("MCPower", "MCPower")
    settings.setValue(_SETTINGS_KEY, mode.value)


# ---------------------------------------------------------------------------
# Theme application
# ---------------------------------------------------------------------------


def apply_theme(mode: ThemeMode | None = None) -> None:
    """Apply the given theme (or load from settings) to QApplication."""
    global _is_dark, _current_mode, _current_style
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        return

    if mode is None:
        mode = saved_theme_mode()

    _current_mode = mode

    if mode == ThemeMode.SYSTEM:
        _is_dark = _detect_system_dark()
    elif mode in (ThemeMode.DARK, ThemeMode.DARK_PINK):
        _is_dark = True
    else:
        _is_dark = False

    # Card colours per theme (QGroupBox frame)
    if mode == ThemeMode.DARK_PINK:
        card_bg, card_border = "#4a3f47", "#6a5a62"
    elif _is_dark:
        card_bg, card_border = "#444444", "#5a5a5a"
    else:
        card_bg, card_border = "#ffffff", "#c8c8c8"

    _current_style = CardProxyStyle(card_bg, card_border)
    app.setStyle(_current_style)

    if mode == ThemeMode.DARK_PINK:
        palette = _build_dark_pink_palette()
    elif _is_dark:
        palette = _build_dark_palette()
    else:
        palette = _build_light_palette()
    app.setPalette(palette)
    app.setStyleSheet(_generate_stylesheet(mode, _is_dark))


def is_dark() -> bool:
    """Return True if the current resolved theme is dark."""
    return _is_dark


def current_mode() -> ThemeMode:
    """Return the currently active theme mode."""
    return _current_mode


def saved_font_size() -> int:
    """Read persisted font size from QSettings. Returns 0 if unset."""
    settings = QSettings("MCPower", "MCPower")
    val = settings.value(_FONT_SIZE_KEY, 0, type=int)
    return val if isinstance(val, int) else 0


def save_font_size(size: int) -> None:
    """Persist font size to QSettings."""
    settings = QSettings("MCPower", "MCPower")
    settings.setValue(_FONT_SIZE_KEY, size)


def _get_default_font_size() -> int:
    """Return the default font size used on first launch."""
    return 10


def apply_font_size(size: int | None = None) -> None:
    """Apply font size to QApplication.

    If *size* is 0 or None, compute system default + 1, persist it, and apply.
    """
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        return
    if not size:
        size = saved_font_size()
    if not size:
        size = _get_default_font_size()
        save_font_size(size)
    font = app.font()
    font.setPointSize(size)
    app.setFont(font)


def current_colors() -> dict[str, str]:
    """Return semantic color hex strings for the current theme.

    For use by widgets that can't rely on QPalette (pyqtgraph, inline styles).
    """
    if _current_mode == ThemeMode.DARK_PINK:
        return {
            "plot_bg": "#282024",
            "plot_fg": "#dcdcdc",
            "muted": "#aa7891",
            "script_bg": "#322830",
            "script_fg": "#dcdcdc",
            "border": "#6a2a4a",
            "success": "#e91e63",
            "error": "#ef5350",
        }
    elif _is_dark:
        return {
            "plot_bg": "#232323",
            "plot_fg": "#dcdcdc",
            "muted": "#8c8c8c",
            "script_bg": "#2d2d2d",
            "script_fg": "#dcdcdc",
            "border": "#505050",
            "success": "#4caf50",
            "error": "#ef5350",
        }
    else:
        return {
            "plot_bg": "#ffffff",
            "plot_fg": "#000000",
            "muted": "#888888",
            "script_bg": "#f5f5f5",
            "script_fg": "#333333",
            "border": "#dddddd",
            "success": "#2e7d32",
            "error": "#c62828",
        }
