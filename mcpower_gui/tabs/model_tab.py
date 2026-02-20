"""Model tab — data upload, formula, variable types, effects, correlations."""

import copy
import csv
import math
from collections import Counter
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui.state import ModelState
from mcpower_gui.theme import current_colors
from mcpower_gui.widgets.anova_factor_editor import AnovaFactorEditor
from mcpower_gui.widgets.correlation_editor import CorrelationEditor, _corr_key
from mcpower_gui.widgets.effects_editor import EffectsEditor
from mcpower_gui.widgets.formula_input import FormulaInput
from mcpower_gui.widgets.info_button import InfoButton, TitleWidgetPositioner, attach_info_button
from mcpower_gui.widgets.cluster_editor import ClusterEditor
from mcpower_gui.widgets.flow_layout import FlowWidget
from mcpower_gui.widgets.tutorial_guide import TutorialGuide
from mcpower_gui.widgets.variable_type_editor import VariableTypeEditor


def _format_level_label(v) -> str:
    """Format a value as a factor level label, matching MCPower backend convention.

    Integer-valued floats become ``"4"`` not ``"4.0"``.
    """
    if isinstance(v, float) and math.isfinite(v) and v == int(v):
        return str(int(v))
    return str(v)


def _attach_readiness_dot(group_box: QGroupBox, title_bold: bool = False) -> QLabel:
    """Attach a readiness dot indicator next to a QGroupBox title."""
    dot = QLabel("○", group_box)
    dot.setFixedSize(20, 20)
    dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
    # x_offset=48: after title gap (22) + info button (20) + spacing (6)
    TitleWidgetPositioner(group_box, dot, x_offset=48, title_bold=title_bold)
    return dot


class ModelTab(QWidget):
    """Composes data upload, FormulaInput, VariableTypeEditor, EffectsEditor,
    CorrelationEditor, and core analysis settings.

    Emits ``model_ready_changed(bool)`` whenever the model becomes ready or
    unready (has valid formula + predictors).
    """

    model_ready_changed = Signal(bool)
    available_tests_changed = Signal(list)
    available_factors_changed = Signal(dict)
    model_type_changed = Signal(str)

    def __init__(self, state: ModelState, parent=None):
        super().__init__(parent)
        self.state = state
        self._data_corr: dict[str, float] = {}
        self._user_corr: dict[str, float] = {}
        self._data_detected: dict[str, dict] = {}
        self._last_emitted_model_type: str | None = None

        # Tab-level layout: tutorial (fixed) + scroll area
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # --- Tutorial Guide (above scroll — always visible) ---
        self._tutorial = TutorialGuide(mode="model")
        self._tutorial.formula_example_requested.connect(self._on_tutorial_formula)
        outer.addWidget(self._tutorial)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        root = QVBoxLayout(content)

        # --- Input Mode Selector ---
        self._input_mode_group = QGroupBox("Input Mode")
        im_layout = QHBoxLayout(self._input_mode_group)

        self._model_type_btn_group = QButtonGroup(self)
        self._model_type_btn_group.setExclusive(True)

        self._btn_linear = QPushButton("Linear Formula")
        self._btn_linear.setCheckable(True)
        self._btn_linear.setChecked(True)
        self._btn_linear.setStyleSheet(self._toggle_btn_style())

        self._btn_anova = QPushButton("ANOVA")
        self._btn_anova.setCheckable(True)
        self._btn_anova.setStyleSheet(self._toggle_btn_style())

        self._model_type_btn_group.addButton(self._btn_linear, 0)
        self._model_type_btn_group.addButton(self._btn_anova, 1)

        im_layout.addWidget(self._btn_linear)
        im_layout.addWidget(self._btn_anova)
        im_layout.addStretch()
        root.addWidget(self._input_mode_group)
        self._input_mode_group.setToolTip(
            "Choose Linear Formula or ANOVA mode for your model"
        )
        attach_info_button(
            self._input_mode_group, "model_tab.md", "Input Mode", "Model Tab"
        )

        self._mode_desc = QLabel("Flexible formula with mixed variable types")
        self._mode_desc.setStyleSheet(
            f"color: {current_colors()['muted']}; font-size: 10px; margin-left: 4px;"
        )
        root.addWidget(self._mode_desc)

        # --- Use Your Data (collapsible) ---
        self._data_group = QGroupBox("Use Your Data (optional)")
        self._data_group.setCheckable(True)
        self._data_group.setChecked(False)
        dg_layout = QVBoxLayout(self._data_group)

        self._data_content = QWidget()
        dc_layout = QVBoxLayout(self._data_content)
        dc_layout.setContentsMargins(0, 0, 0, 0)

        upload_row = QHBoxLayout()
        self._btn_upload = QPushButton("Upload CSV...")
        self._btn_upload.setFixedWidth(120)
        upload_row.addWidget(self._btn_upload)
        self._data_label = QLabel("No data loaded")
        upload_row.addWidget(self._data_label, stretch=1)
        self._btn_clear_data = QPushButton("\u00d7")
        self._btn_clear_data.setFixedSize(48, 48)
        self._btn_clear_data.setFlat(True)
        self._btn_clear_data.setStyleSheet("font-size: 24px;")
        self._btn_clear_data.setToolTip("Remove uploaded data")
        self._btn_clear_data.hide()
        upload_row.addWidget(self._btn_clear_data)
        dc_layout.addLayout(upload_row)

        # Correlation mode radio buttons
        corr_mode_row = QHBoxLayout()
        corr_mode_row.addWidget(QLabel("Correlation mode:"))
        self._corr_mode_group = QButtonGroup(self)
        self._radio_strict = QRadioButton("strict")
        self._radio_partial = QRadioButton("partial")
        self._radio_no = QRadioButton("no")
        self._radio_partial.setChecked(True)
        self._corr_mode_group.addButton(self._radio_strict)
        self._corr_mode_group.addButton(self._radio_partial)
        self._corr_mode_group.addButton(self._radio_no)
        corr_mode_row.addWidget(self._radio_strict)
        corr_mode_row.addWidget(self._radio_partial)
        corr_mode_row.addWidget(self._radio_no)
        corr_mode_row.addStretch()
        dc_layout.addLayout(corr_mode_row)

        # Variable buttons (shown after data upload)
        self._var_buttons_container = FlowWidget(h_spacing=6, v_spacing=4)
        self._var_buttons_container.hide()
        dc_layout.addWidget(self._var_buttons_container)

        self._data_content.hide()
        dg_layout.addWidget(self._data_content)
        self._data_group.toggled.connect(self._data_content.setVisible)

        root.addWidget(self._data_group)
        self._data_group.setToolTip(
            "Upload a CSV file to use real data distributions and correlations"
        )
        attach_info_button(
            self._data_group, "model_tab.md", "Use Your Data (optional)", "Model Tab"
        )

        # --- Linear Formula section (parent wrapper) ---
        self._linear_section = QGroupBox("Linear Formula")
        ls_layout = QVBoxLayout(self._linear_section)

        self._formula_group = QGroupBox("Model Formula")
        fg_layout = QVBoxLayout(self._formula_group)
        self.formula_input = FormulaInput()
        fg_layout.addWidget(self.formula_input)
        ls_layout.addWidget(self._formula_group)
        self._formula_group.setToolTip(
            "R-style formula describing your statistical model"
        )
        _fg_normal = QFont(self._formula_group.font())
        _fg_bold = QFont(_fg_normal)
        _fg_bold.setBold(True)
        self._formula_group.setFont(_fg_bold)
        self.formula_input.setFont(_fg_normal)
        attach_info_button(
            self._formula_group, "model_tab.md", "Model Formula", "Model Tab",
            title_bold=True,
        )
        self._formula_dot = _attach_readiness_dot(self._formula_group, title_bold=True)

        self._types_group = QGroupBox("Variable Types")
        tg_layout = QVBoxLayout(self._types_group)
        self.variable_type_editor = VariableTypeEditor()
        tg_layout.addWidget(self.variable_type_editor)
        ls_layout.addWidget(self._types_group)
        self._types_group.setToolTip(
            "Set each predictor as continuous, binary, or factor"
        )
        attach_info_button(
            self._types_group, "model_tab.md", "Variable Types", "Model Tab"
        )

        root.addWidget(self._linear_section)

        # --- ANOVA section (parent wrapper, hidden by default) ---
        self._anova_section = QGroupBox("ANOVA")
        as_layout = QVBoxLayout(self._anova_section)

        self._anova_group = QGroupBox("ANOVA Factors")
        ag_layout = QVBoxLayout(self._anova_group)
        self.anova_editor = AnovaFactorEditor()
        ag_layout.addWidget(self.anova_editor)
        as_layout.addWidget(self._anova_group)
        _ag_normal = QFont(self._anova_group.font())
        _ag_bold = QFont(_ag_normal)
        _ag_bold.setBold(True)
        self._anova_group.setFont(_ag_bold)
        self.anova_editor.setFont(_ag_normal)
        attach_info_button(
            self._anova_group, "model_tab.md", "Variable Types", "Model Tab",
            title_bold=True,
        )
        self._anova_formula_dot = _attach_readiness_dot(self._anova_group, title_bold=True)

        self._anova_section.hide()
        root.addWidget(self._anova_section)

        # --- Effect Sizes ---
        self._effects_group = QGroupBox()
        eg_layout = QVBoxLayout(self._effects_group)

        # Custom two-row header: bold title + subtitle on left, ? and dot on right
        _effects_header = QWidget()
        _eh_layout = QHBoxLayout(_effects_header)
        _eh_layout.setContentsMargins(0, 0, 0, 4)
        _eh_layout.setSpacing(8)

        _text_col = QVBoxLayout()
        _text_col.setSpacing(1)
        _text_col.setContentsMargins(0, 0, 0, 0)
        _effects_title = QLabel("Effect Sizes")
        _effects_title.setStyleSheet("font-weight: bold;")
        self._effects_subtitle = QLabel(
            "in standardised betas, equal Cohen's D for binary and factor"
        )
        self._effects_subtitle.setStyleSheet(
            f"color: {current_colors()['muted']}; font-size: 10px;"
        )
        _text_col.addWidget(_effects_title)
        _text_col.addWidget(self._effects_subtitle)
        _eh_layout.addLayout(_text_col)

        _effects_info_btn = InfoButton("model_tab.md", "Effect Sizes", "Model Tab")
        self._effects_dot = QLabel("○")
        self._effects_dot.setFixedSize(20, 20)
        self._effects_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _eh_layout.addWidget(_effects_info_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        _eh_layout.addWidget(self._effects_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        _eh_layout.addStretch()

        eg_layout.addWidget(_effects_header)
        self.effects_editor = EffectsEditor()
        eg_layout.addWidget(self.effects_editor)
        root.addWidget(self._effects_group)
        self._effects_group.setToolTip("Standardized effect sizes (betas) for each predictor")

        # --- Cluster Configuration (for mixed models, hidden by default) ---
        self._cluster_group = QGroupBox("Cluster Configuration")
        clg_layout = QVBoxLayout(self._cluster_group)
        self.cluster_editor = ClusterEditor()
        clg_layout.addWidget(self.cluster_editor)
        self._cluster_group.hide()
        root.addWidget(self._cluster_group)
        self._cluster_group.setToolTip(
            "Configure ICC and cluster counts for mixed models"
        )
        attach_info_button(
            self._cluster_group, "model_tab.md", "Cluster Configuration", "Model Tab"
        )

        # --- Correlations (collapsible, hidden in ANOVA mode) ---
        self._corr_group = QGroupBox("Correlations (optional)")
        self._corr_group.setCheckable(True)
        self._corr_group.setChecked(False)
        cg_layout = QVBoxLayout(self._corr_group)
        self.correlation_editor = CorrelationEditor()
        cg_layout.addWidget(self.correlation_editor)
        self.correlation_editor.hide()
        self._corr_group.toggled.connect(self.correlation_editor.setVisible)
        root.addWidget(self._corr_group)
        self._corr_group.setToolTip(
            "Pairwise correlations between continuous/binary predictors"
        )
        attach_info_button(
            self._corr_group, "model_tab.md", "Correlations (optional)", "Model Tab"
        )

        root.addStretch()
        self._scroll.setWidget(content)
        outer.addWidget(self._scroll)

        # --- Connections ---
        self._btn_upload.clicked.connect(self._on_upload)
        self._btn_clear_data.clicked.connect(self._on_clear_data)
        self.formula_input.types_hinted.connect(self._on_types_hinted)
        self.formula_input.formula_changed.connect(self._on_formula_changed)
        self.variable_type_editor.types_changed.connect(self._on_types_changed)
        self.effects_editor.effects_changed.connect(self._on_effects_changed)
        self.correlation_editor.correlations_changed.connect(
            self._on_correlations_changed
        )
        self._corr_mode_group.buttonClicked.connect(self._on_corr_mode_changed)
        self._model_type_btn_group.idClicked.connect(self._on_model_type_btn_clicked)
        self.anova_editor.formula_changed.connect(self._on_anova_formula_changed)
        self.anova_editor.types_changed.connect(self._on_anova_types_changed)
        self.cluster_editor.clusters_changed.connect(self._on_clusters_changed)
        self._data_group.toggled.connect(lambda _: self._update_tutorial())
        self._corr_group.toggled.connect(lambda _: self._update_tutorial())

        self._update_tutorial()
        self._update_readiness_dots()

    # ── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _is_interaction(name: str) -> bool:
        return ":" in name

    def _base_predictors(self) -> list[str]:
        """Return predictors excluding interactions."""
        return [p for p in self.state.predictors if not self._is_interaction(p)]

    def _is_anova_mode(self) -> bool:
        return self.state.model_type == "anova"

    def _get_eligible_columns(self) -> list[str]:
        """Return column names from uploaded data eligible for variable buttons.

        Eligibility rules:
        - No missing values (NaN for numeric, empty string for string columns)
        - ANOVA mode: only columns with 2-12 unique string values
        - Linear mode: numeric columns (any unique count) + string columns
          with 2-12 unique values
        - Excludes the current dependent variable
        """
        data = self.state.uploaded_data
        if data is None:
            return []

        dep_var = self.state.dep_var
        eligible: list[str] = []
        anova = self._is_anova_mode()

        for col, values in data.items():
            if col == dep_var:
                continue

            # Check for missing values
            is_numeric = isinstance(values[0], (int, float)) if values else False
            if is_numeric:
                if any(isinstance(v, float) and math.isnan(v) for v in values):
                    continue
            else:
                if any(v == "" for v in values):
                    continue

            unique_vals = set(_format_level_label(v) for v in values)
            n_unique = len(unique_vals)

            if anova:
                # ANOVA: only string-like columns with 2-12 unique values
                if 2 <= n_unique <= 12:
                    eligible.append(col)
            else:
                # Linear: numeric columns always eligible; string columns
                # only if 2-12 unique values
                if is_numeric:
                    eligible.append(col)
                elif 2 <= n_unique <= 12:
                    eligible.append(col)

        return eligible

    def _get_in_use_variables(self) -> set[str]:
        """Return set of variable names currently in the model."""
        if self._is_anova_mode():
            return self.anova_editor.get_factor_names()
        else:
            return set(self._base_predictors())

    # ── Variable Buttons ────────────────────────────────────

    def _refresh_variable_buttons(self):
        """Rebuild the row of clickable variable buttons from uploaded data."""
        # Clear existing buttons (setParent(None) detaches immediately;
        # deleteLater alone would leave ghosts visible to findChildren)
        for child in list(self._var_buttons_container.findChildren(
            QPushButton, options=Qt.FindChildOption.FindDirectChildrenOnly
        )):
            child.setParent(None)
            child.deleteLater()

        if self.state.uploaded_data is None:
            self._var_buttons_container.hide()
            return

        eligible = self._get_eligible_columns()
        in_use = self._get_in_use_variables()
        available = [col for col in eligible if col not in in_use]

        if not available:
            self._var_buttons_container.hide()
            return

        for name in available:
            btn = QPushButton(name, self._var_buttons_container)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet(
                "QPushButton {"
                "  padding: 3px 10px;"
                "  border: 1px solid palette(mid);"
                "  border-radius: 10px;"
                "  background: palette(button);"
                "}"
                "QPushButton:hover {"
                "  border-color: palette(highlight);"
                "  background: palette(midlight);"
                "}"
            )
            btn.clicked.connect(lambda checked=False, n=name: self._on_var_button_clicked(n))
            btn.show()

        self._var_buttons_container.show()
        self._var_buttons_container.reflow()

    def _on_var_button_clicked(self, name: str):
        """Handle click on a variable button — add variable to the model."""
        if self._is_anova_mode():
            self._add_anova_factor_from_data(name)
        else:
            self._add_linear_variable(name)

    def _add_linear_variable(self, name: str):
        """Add a variable to the linear formula."""
        current = self.formula_input.text().strip()
        if not current:
            self.formula_input.set_formula(f"y = {name}")
        else:
            self.formula_input.set_formula(f"{current} + {name}")

    def _add_anova_factor_from_data(self, name: str):
        """Add a single ANOVA factor from uploaded data."""
        data = self.state.uploaded_data
        if data is None or name not in data:
            return
        values = data[name]
        unique_vals = sorted(set(_format_level_label(v) for v in values))
        n_levels = len(unique_vals)
        counts = Counter(_format_level_label(v) for v in values)
        total = sum(counts.values())
        proportions = [round(counts[label] / total, 4) for label in sorted(counts.keys())]

        factor_def = {
            "name": name,
            "n_levels": n_levels,
            "proportions": proportions,
            "level_labels": unique_vals,
        }
        self.anova_editor.add_data_factor(factor_def)

    # ── Model Type Switching ───────────────────────────────

    @staticmethod
    def _toggle_btn_style() -> str:
        return (
            "QPushButton {"
            "  padding: 3px 10px;"
            "  border: 1px solid palette(mid);"
            "  border-radius: 4px;"
            "  background: palette(button);"
            "  font-weight: bold;"
            "}"
            "QPushButton:checked {"
            "  background: palette(highlight);"
            "  color: palette(highlighted-text);"
            "  border-color: palette(highlight);"
            "}"
            "QPushButton:hover:!checked {"
            "  border-color: palette(highlight);"
            "}"
        )

    def _on_model_type_btn_clicked(self, btn_id: int):
        text = "ANOVA" if btn_id == 1 else "Linear Formula"
        self._on_model_type_changed(text)

    def _on_model_type_changed(self, text: str):
        model_type = "anova" if text == "ANOVA" else "linear_regression"
        self.state.model_type = model_type

        # Clear model state from previous mode
        self.state.formula = ""
        self.state.dep_var = ""
        self.state.predictors = []
        self.state.effects = {}
        self.state.variable_types = {}

        if model_type == "anova":
            self._linear_section.hide()
            self._corr_group.hide()
            self._anova_section.show()
            self._cluster_group.hide()
            self.cluster_editor.clear()
            self.state.cluster_configs = []
            # Apply uploaded data if available, otherwise rebuild from editor state
            if self.state.uploaded_data is not None:
                self._apply_data_to_anova(self.state.uploaded_data)
            else:
                self.anova_editor.refresh()
        else:
            self.anova_editor.clear_data_mode()
            self.state.anova_factors = []
            self.state.anova_interactions = []
            self._linear_section.show()
            self._corr_group.show()
            self._anova_section.hide()
            # Re-apply data-detected types if data is uploaded
            if self.state.uploaded_data is not None and self._data_detected:
                self._apply_data_detected_types()
                self._apply_corr_mode()
            # Re-parse current formula text (if any)
            self.formula_input.set_formula(self.formula_input.text())

        if model_type == "anova":
            self._mode_desc.setText("All predictors are categorical factors")
            self._effects_subtitle.setText(
                "Difference between group and reference in Cohen's D"
            )
        else:
            self._mode_desc.setText("Flexible formula with mixed variable types")
            self._effects_subtitle.setText(
                "in standardised betas, equal Cohen's D for binary and factor"
            )

        self._emit_model_type(model_type)
        self._emit_ready()
        self._update_readiness_dots()
        self._refresh_variable_buttons()
        self._update_tutorial()

    # ── ANOVA signal handlers ─────────────────────────────

    def _on_anova_formula_changed(
        self, formula: str, dep_var: str, predictors: list[str]
    ):
        self.state.formula = formula
        self.state.dep_var = dep_var
        self.state.predictors = list(predictors)

        # Get types from ANOVA editor (all factors)
        self.state.variable_types = self.anova_editor.get_types()
        self.state.anova_factors = self.anova_editor.get_factor_definitions()
        self.state.anova_interactions = self.anova_editor.get_interactions()
        self.state.factor_reference_levels = self.anova_editor.get_reference_levels()
        self.state.factor_level_labels = self.anova_editor.get_level_labels()

        # Rebuild effects editor with factor expansion
        expanded = self._rebuild_effects()

        self._emit_ready()
        self._update_readiness_dots()
        self._emit_available_tests(expanded)
        self._refresh_variable_buttons()
        self._update_tutorial()

    def _on_anova_types_changed(self, types: dict[str, dict]):
        self.state.variable_types = types
        expanded = self._rebuild_effects()
        self._update_readiness_dots()
        self._emit_available_tests(expanded)
        self._update_tutorial()

    # ── Slots ───────────────────────────────────────────────

    @staticmethod
    def _read_csv(path: str) -> dict[str, list]:
        """Read a CSV file into a dict of lists, auto-converting numeric columns."""
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except UnicodeDecodeError:
            with open(path, newline="", encoding="latin-1") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        if not rows:
            raise ValueError("CSV file is empty")
        result: dict[str, list] = {}
        for col in rows[0]:
            if not col or col.startswith("Unnamed"):
                continue
            raw = [r[col] for r in rows]
            try:
                result[col] = [float(v) if v else float("nan") for v in raw]
            except (ValueError, TypeError):
                result[col] = raw
        return result

    def _on_upload(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV files (*.csv)")
        if not path:
            return
        try:
            data = self._read_csv(path)
            self.state.uploaded_data = data
            self.state.data_file_path = path
            fname = Path(path).name
            n_rows = len(next(iter(data.values()))) if data else 0
            columns = list(data.keys())
            self._data_label.setText(
                f"Loaded: {fname} ({n_rows} rows, {len(columns)} columns)"
            )
            self._compute_data_correlations(data)
            self._detect_types_from_data(data)
            if self._is_anova_mode():
                self._apply_data_to_anova(data)
            else:
                self._apply_data_detected_types()
                self._apply_corr_mode()
            self._data_group.setChecked(True)
            self._btn_clear_data.show()
            self._refresh_variable_buttons()
            self._update_tutorial()
        except Exception as exc:
            self._data_label.setText(f"Error: {exc}")
            self.state.uploaded_data = None
            self.state.data_file_path = None
            self._data_detected.clear()
            self._btn_clear_data.hide()
            self.variable_type_editor.set_data_detected_types({})

    def _on_clear_data(self):
        """Remove uploaded data and reset to synthetic generation."""
        self.state.uploaded_data = None
        self.state.data_file_path = None
        self._data_corr.clear()
        self._user_corr.clear()
        self._data_detected.clear()
        self._data_label.setText("No data loaded")
        self._btn_clear_data.hide()
        self.variable_type_editor.set_data_detected_types({})

        if self._is_anova_mode():
            self.anova_editor.clear_data_mode()
            self.anova_editor.refresh()
        else:
            # Reset variable types to defaults (all continuous)
            for name in list(self.state.variable_types.keys()):
                self.state.variable_types[name] = {"type": "continuous"}
            self.variable_type_editor.set_predictors(
                self._base_predictors(), self.state.variable_types
            )
            self.state.variable_types = self.variable_type_editor.get_types()
            self._rebuild_effects()
            self._rebuild_correlation_triangle()

        self._refresh_variable_buttons()
        self._update_tutorial()

    def _detect_types_from_data(self, data: dict[str, list]):
        """Auto-detect variable types from uploaded data.

        Heuristic (matching MCPower model.py):
        - 2 unique values -> binary (with proportion from data)
        - 3-6 unique values -> factor (with n_levels and proportions from data)
        - 7+ unique values -> continuous
        """
        self._data_detected.clear()
        for col, values in data.items():
            unique_vals = sorted(set(_format_level_label(v) for v in values))
            n_unique = len(unique_vals)
            if n_unique == 2:
                # Binary: compute proportion of the higher value
                counts = Counter(_format_level_label(v) for v in values)
                total = sum(counts.values())
                sorted_keys = sorted(counts.keys())
                proportion = round(counts[sorted_keys[-1]] / total, 2)
                self._data_detected[col] = {
                    "type": "binary",
                    "proportion": proportion,
                    "n_unique": n_unique,
                }
            elif 3 <= n_unique <= 6:
                # Factor: compute level proportions and labels
                sorted_labels = sorted(set(_format_level_label(v) for v in values))
                counts = Counter(_format_level_label(v) for v in values)
                total = sum(counts.values())
                proportions = [
                    round(counts[label] / total, 4) for label in sorted(counts.keys())
                ]
                self._data_detected[col] = {
                    "type": "factor",
                    "n_levels": n_unique,
                    "proportions": proportions,
                    "n_unique": n_unique,
                    "level_labels": sorted_labels,
                }
            else:
                self._data_detected[col] = {
                    "type": "continuous",
                    "n_unique": n_unique,
                }

    def _detect_anova_factors_from_data(self, data: dict[str, list]) -> list[dict]:
        """Detect columns suitable as ANOVA factors (2-12 distinct levels)."""
        dep_var = self.anova_editor.get_dep_var()
        factors = []
        for col, values in data.items():
            if col == dep_var:
                continue
            unique_vals = set(_format_level_label(v) for v in values)
            n_unique = len(unique_vals)
            if 2 <= n_unique <= 12:
                sorted_vals = sorted(unique_vals)
                counts = Counter(_format_level_label(v) for v in values)
                total = sum(counts.values())
                proportions = [
                    round(counts[label] / total, 4) for label in sorted(counts.keys())
                ]
                factors.append(
                    {
                        "name": col,
                        "n_levels": n_unique,
                        "proportions": proportions,
                        "level_labels": sorted_vals,
                    }
                )
        return factors

    def _apply_data_to_anova(self, data: dict[str, list]):
        """Apply uploaded data to ANOVA mode — buttons handle factor selection."""
        self.anova_editor.clear_data_mode()
        self.anova_editor.clear_factors()
        self.anova_editor.notify_changed()

    def _apply_data_detected_types(self):
        """Apply detected types to variable_type_editor and state."""
        if not self._data_detected:
            return
        # Update state variable_types for predictors that have detected info
        for name in list(self.state.variable_types.keys()):
            if name in self._data_detected:
                self.state.variable_types[name] = dict(self._data_detected[name])
        # Rebuild variable type editor with detected types
        self.variable_type_editor.set_predictors(
            self._base_predictors(), self.state.variable_types
        )
        self.variable_type_editor.set_data_detected_types(self._data_detected)
        self.state.variable_types = self.variable_type_editor.get_types()
        # Rebuild effects with new types
        expanded = self._rebuild_effects()
        self._emit_available_tests(expanded)

    def _on_types_hinted(self, hints: dict):
        """Pre-populate variable types from an example selection."""
        for name, info in hints.items():
            self.state.variable_types[name] = dict(info)

    def _on_formula_changed(
        self,
        formula: str,
        dep_var: str,
        predictors: list[str],
        random_effects: list[dict] | None = None,
    ):
        self.state.formula = formula
        self.state.dep_var = dep_var
        self.state.predictors = list(predictors)

        # Update cluster editor with random effects
        if random_effects is None:
            random_effects = []
        if random_effects:
            self.cluster_editor.set_random_effects(random_effects, predictors)
            self._cluster_group.show()
            self._emit_model_type("mixed")
        else:
            self.cluster_editor.clear()
            self._cluster_group.hide()
            self.state.cluster_configs = []
            self._emit_model_type("linear_regression")

        # Rebuild variable type editor (base variables only — no interactions)
        self.variable_type_editor.set_predictors(
            self._base_predictors(), self.state.variable_types
        )
        self.state.variable_types = self.variable_type_editor.get_types()

        # Re-apply data-detected types if data is uploaded
        if self._data_detected:
            self._apply_data_detected_types()

        # Rebuild effects editor with factor expansion + predictor types
        expanded = self._rebuild_effects()

        self._rebuild_correlation_triangle()
        self._emit_ready()
        self._update_readiness_dots()
        self._emit_available_tests(expanded)

        self._refresh_variable_buttons()
        self._update_tutorial()

    def _on_types_changed(self, types: dict[str, dict]):
        self.state.variable_types = types

        # Rebuild effects editor with new factor expansion + predictor types
        expanded = self._rebuild_effects()

        self._rebuild_correlation_triangle()
        self._update_readiness_dots()
        self._emit_available_tests(expanded)
        self._update_tutorial()

    def _on_clusters_changed(self, configs: list[dict]):
        self.state.cluster_configs = configs
        self._emit_ready()
        self._update_readiness_dots()
        self._update_tutorial()

    def _on_effects_changed(self, effects: dict[str, float]):
        self.state.effects = effects
        self._update_readiness_dots()
        self._update_tutorial()

    def _expand_predictors(
        self, predictors: list[str], types: dict[str, dict]
    ) -> tuple[list[str], dict[str, str]]:
        """Expand factor predictors into dummy-coded names.

        Returns (expanded_names, predictor_types_dict).
        When level_labels are available (from uploaded data), uses original
        values: e.g. "cyl" with labels ["4","6","8"] → "cyl[6]", "cyl[8]"
        (first label is reference). Otherwise falls back to integer indices:
        "x[2]", "x[3]" (level 1 is reference).

        For interactions, MCPower expands one factor at a time while keeping
        other components as the base name.
        """
        expanded = []
        pred_types: dict[str, str] = {}
        for name in predictors:
            if ":" in name:
                components = name.split(":")
                factor_indices = []
                for idx, comp in enumerate(components):
                    info = types.get(comp, {})
                    if info.get("type") == "factor":
                        factor_indices.append(idx)
                if factor_indices:
                    for fi in factor_indices:
                        comp = components[fi]
                        info = types.get(comp, {})
                        level_labels = info.get("level_labels")
                        if level_labels:
                            reference = level_labels[0]
                            for label in level_labels:
                                if label != reference:
                                    parts = list(components)
                                    parts[fi] = f"{comp}[{label}]"
                                    interaction_name = ":".join(parts)
                                    expanded.append(interaction_name)
                                    pred_types[interaction_name] = "factor"
                        else:
                            n_levels = info.get("n_levels", 3)
                            for lvl in range(2, n_levels + 1):
                                parts = list(components)
                                parts[fi] = f"{comp}[{lvl}]"
                                interaction_name = ":".join(parts)
                                expanded.append(interaction_name)
                                pred_types[interaction_name] = "factor"
                else:
                    expanded.append(name)
                    pred_types[name] = "continuous"
                continue
            info = types.get(name, {})
            vtype = info.get("type", "continuous")
            if vtype == "factor":
                level_labels = info.get("level_labels")
                if level_labels:
                    reference = level_labels[0]
                    for label in level_labels:
                        if label != reference:
                            dummy_name = f"{name}[{label}]"
                            expanded.append(dummy_name)
                            pred_types[dummy_name] = "factor"
                else:
                    n_levels = info.get("n_levels", 3)
                    for lvl in range(2, n_levels + 1):
                        dummy_name = f"{name}[{lvl}]"
                        expanded.append(dummy_name)
                        pred_types[dummy_name] = "factor"
            else:
                expanded.append(name)
                pred_types[name] = vtype
        return expanded, pred_types

    def _rebuild_effects(self) -> list[str]:
        """Expand predictors, rebuild effects editor, sync state. Returns expanded names."""
        expanded, pred_types = self._expand_predictors(
            self.state.predictors, self.state.variable_types
        )
        if self._is_anova_mode():
            factor_refs = self.anova_editor.get_reference_levels()
        else:
            # Derive reference levels from level_labels (first label is reference)
            factor_refs = {}
            for name, info in self.state.variable_types.items():
                level_labels = info.get("level_labels")
                if level_labels:
                    factor_refs[name] = level_labels[0]
            factor_refs = factor_refs or None
        self.effects_editor.set_predictors(
            expanded, self.state.effects, pred_types, factor_refs
        )
        self.state.effects = self.effects_editor.get_effects()
        return expanded

    # ── Correlation management ──────────────────────────────

    def _get_correlable_variables(self) -> list[str]:
        """Return predictor names with type continuous or binary (NOT factor or interaction)."""
        variables = []
        for name in self.state.predictors:
            if self._is_interaction(name):
                continue
            info = self.state.variable_types.get(name, {})
            vtype = info.get("type", "continuous")
            if vtype in ("continuous", "binary"):
                variables.append(name)
        return variables

    def _get_data_backed_variables(self) -> set[str]:
        """Return correlable variables that are present in uploaded data."""
        if self.state.uploaded_data is None:
            return set()
        data_cols = set(self.state.uploaded_data.keys())
        correlable = self._get_correlable_variables()
        return {v for v in correlable if v in data_cols}

    def _rebuild_correlation_triangle(self):
        """Rebuild correlation editor with current correlable variables."""
        if self.state.uploaded_data is not None:
            self._compute_data_correlations(self.state.uploaded_data)
        correlable = self._get_correlable_variables()
        self.correlation_editor.set_variables(correlable)
        self._apply_corr_mode()

    def _get_current_corr_mode(self) -> str:
        if self._radio_strict.isChecked():
            return "strict"
        elif self._radio_no.isChecked():
            return "no"
        return "partial"

    def _apply_corr_mode(self):
        """Apply the current correlation mode to the editor."""
        mode = self._get_current_corr_mode()
        if mode == "strict":
            data_vars = self._get_data_backed_variables()
            if data_vars:
                # Data-backed pairs: locked with data correlations
                # Non-data pairs: editable by user
                merged = dict(self._data_corr)
                merged.update(self._user_corr)
                self.correlation_editor.set_correlations(merged)
                locked = set()
                for key in self.correlation_editor.get_all_keys():
                    v1, v2 = key.split(",")
                    if v1 in data_vars or v2 in data_vars:
                        locked.add(key)
                self.correlation_editor.set_locked_keys(locked)
            else:
                self.correlation_editor.set_enabled(False)
                self.correlation_editor.set_correlations({})
        elif mode == "partial":
            self.correlation_editor.set_enabled(True)
            merged = dict(self._data_corr)
            merged.update(self._user_corr)
            self.correlation_editor.set_correlations(merged)
        else:  # "no"
            self.correlation_editor.set_enabled(True)
            self.correlation_editor.set_correlations(self._user_corr)

        self.state.preserve_correlation = mode
        self.state.correlations = self.correlation_editor.get_correlations()

    def _on_corr_mode_changed(self):
        mode = self._get_current_corr_mode()
        if mode == "partial":
            # Data overrides user edits
            self._user_corr.clear()
        # "no" and "strict": keep _user_corr as-is
        self._apply_corr_mode()

    def _on_correlations_changed(self, correlations: dict[str, float]):
        """User edited a correlation cell."""
        mode = self._get_current_corr_mode()
        if mode == "partial":
            # Store diffs against data correlations
            self._user_corr.clear()
            for key, val in correlations.items():
                data_val = self._data_corr.get(key, 0.0)
                if val != data_val:
                    self._user_corr[key] = val
        elif mode == "strict":
            # Only store user-edited correlations for non-data pairs
            data_vars = self._get_data_backed_variables()
            self._user_corr.clear()
            for key, val in correlations.items():
                v1, v2 = key.split(",")
                if v1 in data_vars or v2 in data_vars:
                    continue  # data-controlled, skip
                if val != 0.0:
                    self._user_corr[key] = val
        elif mode == "no":
            self._user_corr = dict(correlations)

        self.state.correlations = correlations

    def _compute_data_correlations(self, data: dict[str, list]):
        """Compute pairwise correlations from uploaded data for correlable columns."""
        correlable = self._get_correlable_variables()
        cols = [c for c in correlable if c in data]
        self._data_corr.clear()
        if len(cols) < 2:
            return
        try:
            arrays = [np.array(data[c], dtype=float) for c in cols]
        except (ValueError, TypeError):
            return
        corr_matrix = np.corrcoef(np.column_stack(arrays), rowvar=False)
        for i, a in enumerate(cols):
            for j, b in enumerate(cols):
                if i <= j:
                    continue
                key = _corr_key(a, b)
                val = round(float(corr_matrix[i, j]), 2)
                if val != 0.0:
                    self._data_corr[key] = val

    # ── Sync & readiness ────────────────────────────────────

    def sync_state(self):
        """Push all widget values into state before running analysis."""
        self.state.effects = self.effects_editor.get_effects()
        self.state.cluster_configs = self.cluster_editor.get_cluster_configs()
        if self._is_anova_mode():
            self.state.variable_types = self.anova_editor.get_types()
            self.state.anova_factors = self.anova_editor.get_factor_definitions()
            self.state.anova_interactions = self.anova_editor.get_interactions()
            self.state.factor_reference_levels = (
                self.anova_editor.get_reference_levels()
            )
            self.state.factor_level_labels = self.anova_editor.get_level_labels()
            self.state.correlations = {}
            self.state.preserve_correlation = "no"
        else:
            self.state.variable_types = self.variable_type_editor.get_types()
            self.state.preserve_correlation = self._get_current_corr_mode()
            self.state.correlations = self.correlation_editor.get_correlations()

    def _emit_ready(self):
        ready = bool(self.state.formula and self.state.predictors)
        self.model_ready_changed.emit(ready)

    def _emit_model_type(self, model_type: str):
        """Emit model_type_changed only when the type actually changes."""
        if model_type != self._last_emitted_model_type:
            self._last_emitted_model_type = model_type
            self.model_type_changed.emit(model_type)

    @staticmethod
    def _set_dot(dot: QLabel, ok: bool):
        colors = current_colors()
        if ok:
            dot.setText("●")
            dot.setStyleSheet(
                f"color: {colors['success']}; font-size: 21px; background: transparent;"
            )
        else:
            dot.setText("○")
            dot.setStyleSheet(
                f"color: {colors['muted']}; font-size: 21px; background: transparent;"
            )

    def _update_readiness_dots(self):
        s = self.state
        formula_ok = bool(s.formula and s.predictors)
        effects_ok = any(v != 0.0 for v in s.effects.values())
        self._set_dot(self._formula_dot, formula_ok)
        self._set_dot(self._anova_formula_dot, formula_ok)
        self._set_dot(self._effects_dot, effects_ok)

    def _on_tutorial_formula(self, formula: str, types_hint: dict):
        """Fill formula from tutorial example click."""
        if not self._is_anova_mode():
            self.formula_input.load_example(formula, types_hint)

    def _update_tutorial(self):
        """Push current state to tutorial guide."""
        data = self.state.uploaded_data
        data_filename = ""
        data_rows = 0
        if data is not None and self.state.data_file_path:
            data_filename = Path(self.state.data_file_path).name
            first_col = next(iter(data.values()), [])
            data_rows = len(first_col)

        has_clusters = (
            bool(self.state.cluster_configs) or self._cluster_group.isVisible()
        )
        clusters_configured = bool(self.state.cluster_configs) and all(
            c.get("n_clusters", 0) >= 2 or c.get("n_per_parent", 0) >= 2
            for c in self.state.cluster_configs
        )

        self._tutorial.update_state(
            formula=self.state.formula,
            predictors=self.state.predictors,
            effects=self.state.effects,
            variable_types=self.state.variable_types,
            model_type=self.state.model_type,
            data_uploaded=self.state.uploaded_data is not None,
            data_filename=data_filename,
            data_rows=data_rows,
            corr_mode=self._get_current_corr_mode(),
            has_clusters=has_clusters,
            clusters_configured=clusters_configured,
            data_section_open=self._data_group.isChecked(),
            corr_section_open=self._corr_group.isChecked(),
        )

    def reopen_tutorial(self):
        """Re-show the tutorial guide after dismissal."""
        self._tutorial.reopen()

    def _emit_available_tests(self, expanded: list[str]):
        """Emit the list of available target tests based on current predictors."""
        self.available_tests_changed.emit(["overall"] + expanded)

        factors = {
            name: info["n_levels"]
            for name, info in self.state.variable_types.items()
            if info.get("type") == "factor"
        }
        self.available_factors_changed.emit(factors)

    def restore_state(self, snapshot: dict, data_file_path: str | None = None):
        """Restore model tab from a history snapshot."""
        # Clear uploaded data (user must re-upload if needed)
        self.state.uploaded_data = None
        self.state.data_file_path = data_file_path
        self._data_label.setText("No data loaded")
        self._data_corr.clear()
        self._user_corr.clear()
        self._data_detected.clear()
        self.variable_type_editor.set_data_detected_types({})
        self.anova_editor.clear_data_mode()

        has_data = data_file_path is not None
        self._data_group.setChecked(has_data)

        # Restore model type (block signals to avoid clearing state mid-restore)
        model_type = snapshot.get("model_type", "linear_regression")
        self.state.model_type = model_type
        self._model_type_btn_group.blockSignals(True)
        if model_type == "anova":
            self._btn_anova.setChecked(True)
            self._linear_section.hide()
            self._corr_group.hide()
            self._anova_section.show()
        else:
            self._btn_linear.setChecked(True)
            self._linear_section.show()
            self._corr_group.show()
            self._anova_section.hide()
        self._model_type_btn_group.blockSignals(False)

        if model_type == "anova":
            # Restore ANOVA-specific state
            factors = snapshot.get("anova_factors", [])
            interactions = snapshot.get("anova_interactions", [])
            dep_var = snapshot.get("dep_var", "y")
            self.anova_editor.set_dep_var(dep_var)
            self.anova_editor.set_factors(factors, interactions)

            # Restore effects
            effects = snapshot.get("effects", {})
            if effects:
                self.state.effects = dict(effects)
                self._rebuild_effects()
        else:
            # Restore correlation mode radio
            mode = snapshot.get("preserve_correlation", "partial")
            if mode == "strict":
                self._radio_strict.setChecked(True)
            elif mode == "no":
                self._radio_no.setChecked(True)
            else:
                self._radio_partial.setChecked(True)

            # Set formula text — triggers _on_formula_changed which rebuilds
            # variable types, effects, correlations
            formula = snapshot.get("formula", "")
            self.formula_input.set_formula(formula)

            # Restore variable types
            vtypes = snapshot.get("variable_types", {})
            if vtypes:
                self.state.variable_types = {k: dict(v) for k, v in vtypes.items()}
                self.variable_type_editor.set_predictors(
                    self._base_predictors(), self.state.variable_types
                )
                # Trigger effects rebuild with restored types
                self._on_types_changed(self.state.variable_types)

            # Restore effects
            effects = snapshot.get("effects", {})
            if effects:
                self.state.effects = dict(effects)
                self._rebuild_effects()

            # Restore correlations
            correlations = snapshot.get("correlations", {})
            if correlations:
                self._user_corr = dict(correlations)
                self.correlation_editor.set_correlations(correlations)
                self.state.correlations = dict(correlations)

            has_corr = bool(correlations)
            self._corr_group.setChecked(has_corr)

        # Restore cluster configs
        cluster_configs = snapshot.get("cluster_configs", [])
        if cluster_configs:
            self.state.cluster_configs = copy.deepcopy(cluster_configs)
            # Build synthetic random_effects from cluster configs for the editor
            re_list = []
            for cfg in cluster_configs:
                re_info = {
                    "grouping_var": cfg["grouping_var"],
                    "type": "random_slope"
                    if cfg.get("random_slopes")
                    else "random_intercept",
                }
                if cfg.get("random_slopes"):
                    re_info["slope_vars"] = list(cfg["random_slopes"])
                if cfg.get("parent_var"):
                    re_info["parent_var"] = cfg["parent_var"]
                re_list.append(re_info)
            self.cluster_editor.set_random_effects(re_list, self.state.predictors)
            self._cluster_group.show()
        else:
            self.cluster_editor.clear()
            self._cluster_group.hide()

        self._emit_ready()
        self._update_readiness_dots()
