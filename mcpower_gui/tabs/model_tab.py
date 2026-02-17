"""Model tab — data upload, formula, variable types, effects, correlations."""

from pathlib import Path

import pandas as pd
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui.state import ModelState
from mcpower_gui.theme import current_colors
from mcpower_gui.widgets.anova_factor_editor import AnovaFactorEditor
from mcpower_gui.widgets.correlation_editor import CorrelationEditor, _corr_key
from mcpower_gui.widgets.effects_editor import EffectsEditor
from mcpower_gui.widgets.formula_input import FormulaInput
from mcpower_gui.widgets.info_button import attach_info_button
from mcpower_gui.widgets.variable_type_editor import VariableTypeEditor


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

        # Tab-level scroll area wrapping all content
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
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
        attach_info_button(
            self._input_mode_group, "model_tab.md", "Input Mode", "Model Tab"
        )

        # --- Data Upload ---
        data_group = QGroupBox("Data Upload (optional)")
        dg_layout = QVBoxLayout(data_group)

        upload_row = QHBoxLayout()
        self._btn_upload = QPushButton("Upload CSV...")
        self._btn_upload.setFixedWidth(120)
        upload_row.addWidget(self._btn_upload)
        self._data_label = QLabel("No data loaded")
        upload_row.addWidget(self._data_label, stretch=1)
        dg_layout.addLayout(upload_row)

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
        dg_layout.addLayout(corr_mode_row)

        self._columns_label = QLabel("")
        self._columns_label.setWordWrap(True)
        self._columns_label.setStyleSheet(
            f"color: {current_colors()['muted']}; font-size: 11px;"
        )
        dg_layout.addWidget(self._columns_label)

        root.addWidget(data_group)
        attach_info_button(
            data_group, "model_tab.md", "Data Upload (optional)", "Model Tab"
        )

        # --- Linear Formula section (parent wrapper) ---
        self._linear_section = QGroupBox("Linear Formula")
        ls_layout = QVBoxLayout(self._linear_section)

        self._formula_group = QGroupBox("Model Formula")
        fg_layout = QVBoxLayout(self._formula_group)
        self.formula_input = FormulaInput()
        fg_layout.addWidget(self.formula_input)
        ls_layout.addWidget(self._formula_group)
        attach_info_button(
            self._formula_group, "model_tab.md", "Model Formula", "Model Tab"
        )

        self._types_group = QGroupBox("Variable Types")
        tg_layout = QVBoxLayout(self._types_group)
        self.variable_type_editor = VariableTypeEditor()
        tg_layout.addWidget(self.variable_type_editor)
        ls_layout.addWidget(self._types_group)
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
        attach_info_button(
            self._anova_group, "model_tab.md", "Variable Types", "Model Tab"
        )

        self._anova_section.hide()
        root.addWidget(self._anova_section)

        # --- Effect Sizes ---
        effects_group = QGroupBox("Effect Sizes")
        eg_layout = QVBoxLayout(effects_group)
        self.effects_editor = EffectsEditor()
        eg_layout.addWidget(self.effects_editor)
        root.addWidget(effects_group)
        attach_info_button(effects_group, "model_tab.md", "Effect Sizes", "Model Tab")

        # --- Correlations (hidden in ANOVA mode) ---
        self._corr_group = QGroupBox("Correlations (optional)")
        cg_layout = QVBoxLayout(self._corr_group)
        self.correlation_editor = CorrelationEditor()
        cg_layout.addWidget(self.correlation_editor)
        root.addWidget(self._corr_group)
        attach_info_button(
            self._corr_group, "model_tab.md", "Correlations (optional)", "Model Tab"
        )

        root.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        # --- Connections ---
        self._btn_upload.clicked.connect(self._on_upload)
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

    # ── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _is_interaction(name: str) -> bool:
        return ":" in name

    def _base_predictors(self) -> list[str]:
        """Return predictors excluding interactions."""
        return [p for p in self.state.predictors if not self._is_interaction(p)]

    def _is_anova_mode(self) -> bool:
        return self.state.model_type == "anova"

    # ── Model Type Switching ───────────────────────────────

    @staticmethod
    def _toggle_btn_style() -> str:
        return (
            "QPushButton {"
            "  padding: 3px 10px;"
            "  border: 1px solid palette(mid);"
            "  border-radius: 4px;"
            "  background: palette(button);"
            "}"
            "QPushButton:checked {"
            "  background: palette(highlight);"
            "  color: palette(highlighted-text);"
            "  font-weight: bold;"
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

        self.model_type_changed.emit(model_type)
        self._emit_ready()

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
        self._emit_available_tests(expanded)

    def _on_anova_types_changed(self, types: dict[str, dict]):
        self.state.variable_types = types
        expanded = self._rebuild_effects()
        self._emit_available_tests(expanded)

    # ── Slots ───────────────────────────────────────────────

    def _on_upload(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV files (*.csv)")
        if not path:
            return
        try:
            df = pd.read_csv(path)
            self.state.uploaded_data = df
            self.state.data_file_path = path
            fname = Path(path).name
            self._data_label.setText(
                f"Loaded: {fname} ({len(df)} rows, {len(df.columns)} columns)"
            )
            self._columns_label.setText(f"Columns: {', '.join(df.columns.tolist())}")
            self._compute_data_correlations(df)
            self._detect_types_from_data(df)
            if self._is_anova_mode():
                self._apply_data_to_anova(df)
            else:
                self._apply_data_detected_types()
                self._apply_corr_mode()
        except Exception as exc:
            self._data_label.setText(f"Error: {exc}")
            self._columns_label.setText("")
            self.state.uploaded_data = None
            self.state.data_file_path = None
            self._data_detected.clear()
            self.variable_type_editor.set_data_detected_types({})

    def _detect_types_from_data(self, df: pd.DataFrame):
        """Auto-detect variable types from uploaded data.

        Heuristic (matching MCPower model.py):
        - 2 unique values -> binary (with proportion from data)
        - 3-6 unique values -> factor (with n_levels and proportions from data)
        - 7+ unique values -> continuous
        """
        self._data_detected.clear()
        for col in df.columns:
            n_unique = df[col].nunique()
            if n_unique == 2:
                # Binary: compute proportion of the higher value
                counts = df[col].value_counts(normalize=True).sort_index()
                proportion = round(float(counts.iloc[-1]), 2)
                self._data_detected[col] = {
                    "type": "binary",
                    "proportion": proportion,
                    "n_unique": n_unique,
                }
            elif 3 <= n_unique <= 6:
                # Factor: compute level proportions and labels
                vals = df[col].dropna().unique()
                sorted_labels = sorted(str(v) for v in vals)
                counts = df[col].value_counts(normalize=True).sort_index()
                proportions = [round(float(v), 4) for v in counts.values]
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

    def _detect_anova_factors_from_data(self, df: pd.DataFrame) -> list[dict]:
        """Detect columns suitable as ANOVA factors (2-12 distinct levels)."""
        dep_var = self.anova_editor.get_dep_var()
        factors = []
        for col in df.columns:
            if col == dep_var:
                continue
            try:
                vals = df[col].dropna().unique()
            except Exception:
                continue
            n_unique = len(vals)
            if 2 <= n_unique <= 12:
                sorted_vals = sorted(str(v) for v in vals)
                counts = df[col].value_counts(normalize=True).sort_index()
                proportions = [round(float(v), 4) for v in counts.values]
                factors.append(
                    {
                        "name": col,
                        "n_levels": n_unique,
                        "proportions": proportions,
                        "level_labels": sorted_vals,
                    }
                )
        return factors

    def _apply_data_to_anova(self, df: pd.DataFrame):
        """Apply uploaded data to ANOVA factor editor."""
        factors = self._detect_anova_factors_from_data(df)
        if not factors:
            self._data_label.setText(
                self._data_label.text() + " (no columns with 2–12 levels found)"
            )
            return
        self.anova_editor.set_data_factors(factors)

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

    def _on_formula_changed(self, formula: str, dep_var: str, predictors: list[str]):
        self.state.formula = formula
        self.state.dep_var = dep_var
        self.state.predictors = list(predictors)

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
        self._emit_available_tests(expanded)

    def _on_types_changed(self, types: dict[str, dict]):
        self.state.variable_types = types

        # Rebuild effects editor with new factor expansion + predictor types
        expanded = self._rebuild_effects()

        self._rebuild_correlation_triangle()
        self._emit_available_tests(expanded)

    def _on_effects_changed(self, effects: dict[str, float]):
        self.state.effects = effects

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
        factor_refs = (
            self.anova_editor.get_reference_levels() if self._is_anova_mode() else None
        )
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
        data_cols = set(self.state.uploaded_data.columns)
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

    def _compute_data_correlations(self, df: pd.DataFrame):
        """Compute pairwise correlations from uploaded data for correlable columns."""
        correlable = self._get_correlable_variables()
        cols = [c for c in correlable if c in df.columns]
        self._data_corr.clear()
        if len(cols) < 2:
            return
        corr_matrix = df[cols].corr()
        for i, a in enumerate(cols):
            for j, b in enumerate(cols):
                if i <= j:
                    continue
                key = _corr_key(a, b)
                val = round(corr_matrix.iloc[i, j], 2)
                if val != 0.0:
                    self._data_corr[key] = val

    # ── Sync & readiness ────────────────────────────────────

    def sync_state(self):
        """Push all widget values into state before running analysis."""
        self.state.effects = self.effects_editor.get_effects()
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
        self._columns_label.setText("")
        self._data_corr.clear()
        self._user_corr.clear()
        self._data_detected.clear()
        self.variable_type_editor.set_data_detected_types({})
        self.anova_editor.clear_data_mode()

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

        self._emit_ready()
