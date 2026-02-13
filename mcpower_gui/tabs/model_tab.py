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
from mcpower_gui.widgets.correlation_editor import CorrelationEditor, _corr_key
from mcpower_gui.widgets.effects_editor import EffectsEditor
from mcpower_gui.widgets.formula_input import FormulaInput
from mcpower_gui.widgets.variable_type_editor import VariableTypeEditor


class ModelTab(QWidget):
    """Composes data upload, FormulaInput, VariableTypeEditor, EffectsEditor,
    CorrelationEditor, and core analysis settings.

    Emits ``model_ready_changed(bool)`` whenever the model becomes ready or
    unready (has valid formula + predictors).
    """

    model_ready_changed = Signal(bool)
    available_tests_changed = Signal(list)

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
        self._columns_label.setStyleSheet("color: #888; font-size: 11px;")
        dg_layout.addWidget(self._columns_label)

        root.addWidget(data_group)

        # --- Formula ---
        formula_group = QGroupBox("Model Formula")
        fg_layout = QVBoxLayout(formula_group)
        self.formula_input = FormulaInput()
        fg_layout.addWidget(self.formula_input)
        root.addWidget(formula_group)

        # --- Variable Types ---
        types_group = QGroupBox("Variable Types")
        tg_layout = QVBoxLayout(types_group)
        self.variable_type_editor = VariableTypeEditor()
        tg_layout.addWidget(self.variable_type_editor)
        root.addWidget(types_group)

        # --- Effect Sizes ---
        effects_group = QGroupBox("Effect Sizes")
        eg_layout = QVBoxLayout(effects_group)
        self.effects_editor = EffectsEditor()
        eg_layout.addWidget(self.effects_editor)
        root.addWidget(effects_group)

        # --- Correlations ---
        corr_group = QGroupBox("Correlations (optional)")
        cg_layout = QVBoxLayout(corr_group)
        self.correlation_editor = CorrelationEditor()
        cg_layout.addWidget(self.correlation_editor)
        root.addWidget(corr_group)

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

    # ── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _is_interaction(name: str) -> bool:
        return ":" in name

    def _base_predictors(self) -> list[str]:
        """Return predictors excluding interactions."""
        return [p for p in self.state.predictors if not self._is_interaction(p)]

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
                # Factor: compute level proportions
                counts = df[col].value_counts(normalize=True).sort_index()
                proportions = [round(float(v), 4) for v in counts.values]
                self._data_detected[col] = {
                    "type": "factor",
                    "n_levels": n_unique,
                    "proportions": proportions,
                    "n_unique": n_unique,
                }
            else:
                self._data_detected[col] = {
                    "type": "continuous",
                    "n_unique": n_unique,
                }

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
        A factor with n_levels=3 named "x" becomes "x[2]", "x[3]"
        (level 1 is the reference).
        """
        expanded = []
        pred_types: dict[str, str] = {}
        for name in predictors:
            if ":" in name:
                components = name.split(":")
                has_factor = False
                all_expansions = []
                for comp in components:
                    info = types.get(comp, {})
                    if info.get("type") == "factor":
                        has_factor = True
                        n_levels = info.get("n_levels", 3)
                        all_expansions.append(
                            [f"{comp}[{lvl}]" for lvl in range(2, n_levels + 1)]
                        )
                    else:
                        all_expansions.append([comp])
                if has_factor:
                    from itertools import product as iter_product

                    for combo in iter_product(*all_expansions):
                        interaction_name = ":".join(combo)
                        expanded.append(interaction_name)
                        pred_types[interaction_name] = "factor"
                else:
                    expanded.append(name)
                    pred_types[name] = "continuous"
                continue
            info = types.get(name, {})
            vtype = info.get("type", "continuous")
            if vtype == "factor":
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
        self.effects_editor.set_predictors(expanded, self.state.effects, pred_types)
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
        self.state.variable_types = self.variable_type_editor.get_types()
        self.state.preserve_correlation = self._get_current_corr_mode()
        self.state.correlations = self.correlation_editor.get_correlations()

    def _emit_ready(self):
        ready = bool(self.state.formula and self.state.predictors)
        self.model_ready_changed.emit(ready)

    def _emit_available_tests(self, expanded: list[str]):
        """Emit the list of available target tests based on current predictors."""
        self.available_tests_changed.emit(["overall"] + expanded)

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
