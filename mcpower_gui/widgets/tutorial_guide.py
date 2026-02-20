"""Contextual tutorial guide — shows next steps based on model state."""

from __future__ import annotations

__all__ = ["TutorialGuide", "is_tutorial_enabled", "set_tutorial_enabled"]

from pathlib import Path

import yaml
from PySide6.QtCore import QSettings, Signal, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui.theme import current_colors
from mcpower_gui.widgets.formula_input import EXAMPLES as _FORMULA_EXAMPLES
from mcpower_gui.widgets.tip_engine import TipEngine

# Load tip rules once at module level (graceful fallback if file is missing)
try:
    _TIPS_PATH = Path(__file__).resolve().parent.parent / "tips.yaml"
    with open(_TIPS_PATH) as _f:  # noqa: PTH123
        _ALL_RULES = yaml.safe_load(_f)
    _ENGINE = TipEngine(_ALL_RULES)
except Exception:
    _ALL_RULES = []
    _ENGINE = TipEngine([])


class TutorialGuide(QWidget):
    """Dynamic guide showing done / next steps / optional actions.

    Operates in two modes:
    - "model": full guide for the Model tab
    - "analysis": condensed guide for the Analysis tab

    Emits signals when clickable items are activated:
    - formula_example_requested(str, dict): user clicked a formula example
    - navigate_tab_requested(str): user wants to switch to "model" or "analysis" tab
    """

    formula_example_requested = Signal(str, dict)
    navigate_tab_requested = Signal(str)

    _SETTINGS_KEY = "show_tutorial_guide"

    def __init__(self, mode: str = "model", parent: QWidget | None = None):
        super().__init__(parent)
        self._mode = mode
        self._dismissed = False

        # Check persistent setting
        settings = QSettings("MCPower", "MCPower")
        if not settings.value(self._SETTINGS_KEY, True, type=bool):
            self._dismissed = True

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 6, 8, 6)
        self._layout.setSpacing(2)

        # State cache for rebuild
        self._state_cache: dict = {}
        self._rendered_tips: list | None = None

        if self._dismissed:
            self.hide()

    def update_state(
        self,
        formula: str = "",
        predictors: list[str] | None = None,
        effects: dict[str, float] | None = None,
        variable_types: dict[str, dict] | None = None,
        model_type: str = "linear_regression",
        data_uploaded: bool = False,
        data_filename: str = "",
        data_rows: int = 0,
        corr_mode: str = "partial",
        has_clusters: bool = False,
        clusters_configured: bool = False,
        model_ready: bool = False,
        data_section_open: bool = False,
        corr_section_open: bool = False,
    ):
        """Rebuild the guide content based on current model state."""
        if self._dismissed:
            return

        predictors = predictors or []
        effects = effects or {}
        variable_types = variable_types or {}

        self._state_cache = {
            "formula": formula,
            "predictors": predictors,
            "effects": effects,
            "variable_types": variable_types,
            "model_type": model_type,
            "data_uploaded": data_uploaded,
            "data_filename": data_filename,
            "data_rows": data_rows,
            "corr_mode": corr_mode,
            "has_clusters": has_clusters,
            "clusters_configured": clusters_configured,
            "model_ready": model_ready,
            "data_section_open": data_section_open,
            "corr_section_open": corr_section_open,
        }

        engine_state = self._build_engine_state()
        tips = _ENGINE.evaluate(engine_state)
        if tips == self._rendered_tips:
            return
        self._render(tips)
        self.show()

    def _build_engine_state(self) -> dict:
        """Convert the raw state cache to the engine-compatible state dict."""
        s = self._state_cache
        predictors = s["predictors"]
        effects = s["effects"]
        variable_types = s["variable_types"]
        model_type = s["model_type"]

        has_effects = any(v != 0.0 for v in effects.values())
        has_non_continuous = any(
            info.get("type") != "continuous" for info in variable_types.values()
        )
        correlable_count = sum(
            1
            for name in predictors
            if ":" not in name
            and variable_types.get(name, {}).get("type", "continuous")
            in ("continuous", "binary")
        )
        has_factors = any(
            info.get("type") == "factor" for info in variable_types.values()
        )
        n_predictors = len([p for p in predictors if ":" not in p])

        has_clusters = s["has_clusters"]
        clusters_configured = s["clusters_configured"]

        return {
            "tab": self._mode,
            "mode": "anova" if model_type == "anova" else "linear",
            "formula": s["formula"],
            "formula_display": s["formula"],
            "has_effects": has_effects,
            "has_non_continuous": has_non_continuous,
            "has_clusters": has_clusters,
            "clusters_configured": clusters_configured,
            "clusters_resolved": not has_clusters or clusters_configured,
            "data_uploaded": s["data_uploaded"],
            "data_filename": s["data_filename"],
            "data_rows": s["data_rows"],
            "corr_mode": s["corr_mode"],
            "correlable_count": correlable_count,
            "data_section_open": s["data_section_open"],
            "corr_section_open": s["corr_section_open"],
            "model_ready": s["model_ready"],
            "has_factors": has_factors,
            "n_predictors": n_predictors,
        }

    def _render(self, tips: list) -> None:
        """Clear and re-render tips from engine output."""
        self._rendered_tips = list(tips)
        self._clear()
        for tip in tips:
            if tip.tip_type == "formula_examples":
                self._add_formula_examples()
            else:
                self._add_line(tip.text, tip.style)
        self._add_dismiss_button()
        self._apply_card_style()

    def _clear(self):
        """Remove all child widgets from layout."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            sub = item.layout()
            if sub:
                while sub.count():
                    child = sub.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

    def _add_line(self, text: str, style: str = "normal"):
        """Add a styled text line.

        Styles: "done" (muted), "next" (bold), "optional" (muted),
        "normal" (default).
        """
        colors = current_colors()
        label = QLabel(text)
        label.setWordWrap(True)
        if style == "done":
            label.setStyleSheet(f"color: {colors['success']}; padding: 0; margin: 0;")
        elif style == "next":
            label.setStyleSheet("font-weight: bold; padding: 0; margin: 0;")
        elif style == "optional":
            label.setStyleSheet(f"color: {colors['muted']}; padding: 0; margin: 0;")
        else:
            label.setStyleSheet("padding: 0; margin: 0;")
        self._layout.addWidget(label)

    def _add_formula_examples(self):
        """Add clickable formula example buttons."""
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 2, 0, 2)
        h.addWidget(QLabel("   Try:"))
        colors = current_colors()
        for label, formula, types_hint in _FORMULA_EXAMPLES:
            btn = QPushButton(label)
            btn.setFlat(True)
            btn.setToolTip(formula)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{ color: {colors['success']}; text-decoration: underline; "
                f"border: none; padding: 2px 6px; }}"
                f"QPushButton:hover {{ background: rgba(128,128,128,0.15); border-radius: 3px; }}"
            )
            btn.clicked.connect(
                lambda _, f=formula, t=types_hint: self.formula_example_requested.emit(f, t)
            )
            h.addWidget(btn)
        h.addStretch()
        self._layout.addWidget(row)

    def _add_dismiss_button(self):
        """Add a dismiss [x] button to the top-right corner."""
        # We insert a header row with stretch + dismiss button
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.addStretch()
        btn = QPushButton("\u00d7")
        btn.setFixedSize(40, 40)
        btn.setStyleSheet("font-size: 20px;")
        btn.setFlat(True)
        btn.setToolTip("Dismiss guide for this session")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._on_dismiss)
        h.addWidget(btn)
        self._layout.insertWidget(0, row)

    def _apply_card_style(self):
        """Apply a subtle card background."""
        colors = current_colors()
        border = colors["border"]
        self.setStyleSheet(
            f"TutorialGuide {{ background: rgba(128,128,128,0.06); "
            f"border: 1px solid {border}; border-radius: 6px; }}"
        )

    def _on_dismiss(self):
        """Hide the guide for this session."""
        self._dismissed = True
        self.hide()

    def reopen(self):
        """Re-show the guide after a session dismiss."""
        self._dismissed = False
        self._rendered_tips = None
        if self._state_cache:
            engine_state = self._build_engine_state()
            tips = _ENGINE.evaluate(engine_state)
            self._render(tips)
            self.show()


def is_tutorial_enabled() -> bool:
    """Check if the tutorial guide is enabled in settings."""
    settings = QSettings("MCPower", "MCPower")
    return settings.value(TutorialGuide._SETTINGS_KEY, True, type=bool)


def set_tutorial_enabled(enabled: bool) -> None:
    """Persist tutorial guide setting."""
    settings = QSettings("MCPower", "MCPower")
    settings.setValue(TutorialGuide._SETTINGS_KEY, enabled)
