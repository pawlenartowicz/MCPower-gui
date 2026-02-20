"""Settings dialog — sidebar navigation with General + Scenarios pages."""

from __future__ import annotations

import os

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui.widgets.spin_boxes import DoubleSpinBox, SpinBox

from mcpower_gui import __version__
from mcpower_gui.state import SCENARIO_DEFAULTS, ModelState
from mcpower_gui.theme import (
    ThemeMode,
    apply_font_size,
    apply_theme,
    save_font_size,
    save_theme_mode,
    saved_font_size,
    saved_theme_mode,
)
from mcpower_gui.widgets.info_button import attach_info_button


class SettingsDialog(QDialog):
    """Modal dialog for configuring simulations, alpha, seed, parallel, and
    scenario parameters.  Writes to *state* only on Accept.
    """

    reopen_tips_requested = Signal()

    def __init__(self, state: ModelState, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(700, 500)
        self._state = state
        self._original_theme = saved_theme_mode()
        self._original_font_size = saved_font_size()

        root = QVBoxLayout(self)

        # ── Sidebar + stacked pages ─────────────────────────
        body = QHBoxLayout()

        self._sidebar = QListWidget()
        self._sidebar.setFixedWidth(140)
        self._sidebar.addItem("General")
        self._sidebar.addItem("Scenarios")
        body.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        body.addWidget(self._stack, stretch=1)

        root.addLayout(body, stretch=1)

        # ── Page 0: General ─────────────────────────────────
        general_page = self._build_general_page(state)
        self._stack.addWidget(general_page)

        # ── Page 1: Scenarios ───────────────────────────────
        scenarios_page = self._build_scenarios_page(state)
        self._stack.addWidget(scenarios_page)

        # ── Buttons ─────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._apply_and_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._sidebar.currentRowChanged.connect(self._stack.setCurrentIndex)
        self._sidebar.setCurrentRow(0)

    # ── Page builders ────────────────────────────────────────

    def _build_general_page(self, state: ModelState) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        page = QWidget()
        page_layout = QVBoxLayout(page)

        general = QGroupBox("General")
        gf = QFormLayout(general)

        gf.addRow("Version:", QLabel(__version__))

        self._theme = QComboBox()
        self._theme.addItem("System", ThemeMode.SYSTEM.value)
        self._theme.addItem("Light", ThemeMode.LIGHT.value)
        self._theme.addItem("Dark", ThemeMode.DARK.value)
        self._theme.addItem("Dark Pink", ThemeMode.DARK_PINK.value)
        current = saved_theme_mode()
        _theme_map = {
            ThemeMode.SYSTEM: 0,
            ThemeMode.LIGHT: 1,
            ThemeMode.DARK: 2,
            ThemeMode.DARK_PINK: 3,
        }
        self._theme.setCurrentIndex(_theme_map.get(current, 0))
        self._theme.currentIndexChanged.connect(self._on_theme_changed)
        gf.addRow("Theme:", self._theme)

        self._font_size = SpinBox()
        self._font_size.setRange(8, 20)
        cur_size = saved_font_size()
        self._font_size.setValue(cur_size if cur_size else 10)
        self._font_size.valueChanged.connect(self._on_font_size_changed)
        gf.addRow("Font size:", self._font_size)

        self._reopen_tips_btn = QPushButton("Reopen Tips")
        self._reopen_tips_btn.setFixedWidth(120)
        self._reopen_tips_btn.setToolTip(
            "Re-show the tutorial hints if you dismissed them"
        )
        self._reopen_tips_btn.clicked.connect(self._on_reopen_tips)
        gf.addRow("Tutorial tips:", self._reopen_tips_btn)

        self._n_simulations = SpinBox()
        self._n_simulations.setRange(100, 100_000)
        self._n_simulations.setValue(state.n_simulations)
        self._n_simulations.setSingleStep(100)
        gf.addRow("Simulations (OLS):", self._n_simulations)

        self._n_simulations_mixed = SpinBox()
        self._n_simulations_mixed.setRange(100, 100_000)
        self._n_simulations_mixed.setValue(state.n_simulations_mixed_model)
        self._n_simulations_mixed.setSingleStep(100)
        gf.addRow("Simulations (mixed):", self._n_simulations_mixed)

        self._alpha = DoubleSpinBox()
        self._alpha.setRange(0.001, 0.5)
        self._alpha.setValue(state.alpha)
        self._alpha.setSingleStep(0.005)
        self._alpha.setDecimals(3)
        gf.addRow("Alpha:", self._alpha)

        # QDoubleSpinBox with decimals=0 because QSpinBox max is ~2.1B
        self._seed = DoubleSpinBox()
        self._seed.setDecimals(0)
        self._seed.setRange(0, 3_000_000_000)
        self._seed.setValue(state.seed)
        self._seed.setSingleStep(1)
        gf.addRow("Seed:", self._seed)

        self._max_failed = DoubleSpinBox()
        self._max_failed.setRange(0.0, 1.0)
        self._max_failed.setValue(state.max_failed_simulations)
        self._max_failed.setSingleStep(0.01)
        self._max_failed.setDecimals(2)
        gf.addRow("Max failed sims:", self._max_failed)

        self._parallel = QComboBox()
        self._parallel.addItem("Off", False)
        self._parallel.addItem("On", True)
        self._parallel.addItem("Mixed models only", "mixedmodels")
        # Select current value
        _par_map = {False: 0, True: 1, "mixedmodels": 2}
        self._parallel.setCurrentIndex(_par_map.get(state.parallel, 0))
        gf.addRow("Parallel:", self._parallel)

        cpu_count = os.cpu_count() or 4
        half_cores = max(1, cpu_count // 2)
        all_minus_one = max(1, cpu_count - 1)

        self._cores_mode = QComboBox()
        self._cores_mode.addItem(f"All - 1 ({all_minus_one})", all_minus_one)
        self._cores_mode.addItem(f"Half ({half_cores})", half_cores)
        self._cores_mode.addItem("Custom", "custom")
        gf.addRow("N cores:", self._cores_mode)

        self._n_cores = SpinBox()
        self._n_cores.setRange(1, cpu_count)
        self._n_cores.setValue(min(state.n_cores, cpu_count))
        self._n_cores.setVisible(False)
        gf.addRow("", self._n_cores)

        # Match current state.n_cores to a preset
        if state.n_cores == all_minus_one:
            self._cores_mode.setCurrentIndex(0)
        elif state.n_cores == half_cores:
            self._cores_mode.setCurrentIndex(1)
        else:
            self._cores_mode.setCurrentIndex(2)
            self._n_cores.setVisible(True)

        def _on_cores_mode_changed(idx):
            is_custom = self._cores_mode.currentData() == "custom"
            self._n_cores.setVisible(is_custom)

        self._cores_mode.currentIndexChanged.connect(_on_cores_mode_changed)

        # Disable cores section when parallel is off
        cores_enabled = state.parallel is not False

        self._cores_mode.setEnabled(cores_enabled)
        self._n_cores.setEnabled(cores_enabled)

        self._parallel.currentIndexChanged.connect(
            lambda idx: (
                self._cores_mode.setEnabled(idx != 0),
                self._n_cores.setEnabled(idx != 0),
            )
        )

        page_layout.addWidget(general)
        attach_info_button(general, "general_settings.md")
        page_layout.addStretch()

        scroll.setWidget(page)
        return scroll

    def _build_scenarios_page(self, state: ModelState) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        page = QWidget()
        page_layout = QVBoxLayout(page)

        self._scenario_spins: dict[str, dict] = {}
        self._scenario_combos: dict[str, dict[str, QComboBox]] = {}
        for scenario_name, defaults in SCENARIO_DEFAULTS.items():
            title = f"Scenario: {scenario_name.capitalize()}"
            if scenario_name == "optimistic":
                title += " (default)"
            cfg = state.scenario_configs.get(scenario_name, {})
            group, spins, combos = self._build_scenario_group(title, cfg, defaults)
            self._scenario_spins[scenario_name] = spins
            self._scenario_combos[scenario_name] = combos
            page_layout.addWidget(group)

        page_layout.addStretch()

        scroll.setWidget(page)
        return scroll

    # ── Helpers ──────────────────────────────────────────────

    _SPIN_CONFIGS = {
        "heterogeneity": ("Heterogeneity:", 0, 2),
        "heteroskedasticity": ("Heteroskedasticity:", -1, 1),
        "correlation_noise_sd": ("Correlation noise SD:", 0, 2),
        "distribution_change_prob": ("Distribution change prob:", 0, 1),
    }

    _DIST_OPTIONS = ["normal", "heavy_tailed", "skewed"]
    _DIST_ITEMS = [
        ("normal", "Normal"),
        ("heavy_tailed", "Heavy tailed"),
        ("skewed", "Skewed"),
    ]

    def _build_scenario_group(
        self, title: str, cfg: dict, defaults: dict
    ) -> tuple[QGroupBox, dict, dict[str, QComboBox]]:
        """Create a scenario group box with OLS + LME perturbation controls."""
        group = QGroupBox(title)
        form = QFormLayout(group)
        spins: dict = {}
        combos: dict[str, QComboBox] = {}

        # ── OLS / General perturbations ─────────────────────────
        for key, (label, lo, hi) in self._SPIN_CONFIGS.items():
            spin = DoubleSpinBox()
            spin.setRange(lo, hi)
            spin.setSingleStep(0.05)
            spin.setDecimals(2)
            spin.setValue(cfg.get(key, defaults[key]))
            form.addRow(label, spin)
            spins[key] = spin

        # ── Mixed Effects Perturbations ──────────────────────────
        sep = QLabel("Mixed Effects Perturbations")
        sep.setStyleSheet("color: gray; font-style: italic; padding-top: 6px;")
        form.addRow(sep)

        # icc_noise_sd
        icc_spin = DoubleSpinBox()
        icc_spin.setRange(0.0, 2.0)
        icc_spin.setSingleStep(0.05)
        icc_spin.setDecimals(2)
        icc_spin.setValue(cfg.get("icc_noise_sd", defaults.get("icc_noise_sd", 0.0)))
        form.addRow("ICC noise SD:", icc_spin)
        spins["icc_noise_sd"] = icc_spin

        # random_effect_dist
        re_dist_combo = QComboBox()
        for val, lbl in self._DIST_ITEMS:
            re_dist_combo.addItem(lbl, val)
        re_val = cfg.get(
            "random_effect_dist", defaults.get("random_effect_dist", "normal")
        )
        re_dist_combo.setCurrentIndex(
            self._DIST_OPTIONS.index(re_val) if re_val in self._DIST_OPTIONS else 0
        )
        form.addRow("Random effect dist:", re_dist_combo)
        combos["random_effect_dist"] = re_dist_combo

        # random_effect_df
        re_df_spin = SpinBox()
        re_df_spin.setRange(2, 50)
        re_df_spin.setValue(
            cfg.get("random_effect_df", defaults.get("random_effect_df", 5))
        )
        form.addRow("Random effect df:", re_df_spin)
        spins["random_effect_df"] = re_df_spin

        # residual_dist
        res_dist_combo = QComboBox()
        for val, lbl in self._DIST_ITEMS:
            res_dist_combo.addItem(lbl, val)
        res_val = cfg.get("residual_dist", defaults.get("residual_dist", "normal"))
        res_dist_combo.setCurrentIndex(
            self._DIST_OPTIONS.index(res_val) if res_val in self._DIST_OPTIONS else 0
        )
        form.addRow("Residual dist:", res_dist_combo)
        combos["residual_dist"] = res_dist_combo

        # residual_change_prob
        res_prob_spin = DoubleSpinBox()
        res_prob_spin.setRange(0.0, 1.0)
        res_prob_spin.setSingleStep(0.05)
        res_prob_spin.setDecimals(2)
        res_prob_spin.setValue(
            cfg.get("residual_change_prob", defaults.get("residual_change_prob", 0.0))
        )
        form.addRow("Residual change prob:", res_prob_spin)
        spins["residual_change_prob"] = res_prob_spin

        # residual_df
        res_df_spin = SpinBox()
        res_df_spin.setRange(2, 50)
        res_df_spin.setValue(cfg.get("residual_df", defaults.get("residual_df", 10)))
        form.addRow("Residual df:", res_df_spin)
        spins["residual_df"] = res_df_spin

        attach_info_button(group, "scenario_settings.md")
        return group, spins, combos

    def _on_reopen_tips(self):
        """Emit signal to reopen tutorial tips in the main window."""
        self.reopen_tips_requested.emit()

    def _on_theme_changed(self):
        """Live-preview the selected theme."""
        mode = ThemeMode(self._theme.currentData())
        apply_theme(mode)

    def _on_font_size_changed(self, value: int):
        """Live-preview the selected font size."""
        apply_font_size(value)

    def reject(self):
        """Revert theme and font size to original on Cancel."""
        apply_theme(self._original_theme)
        apply_font_size(self._original_font_size)
        super().reject()

    def _apply_and_accept(self):
        """Write widget values to state and close."""
        s = self._state
        s.n_simulations = self._n_simulations.value()
        s.n_simulations_mixed_model = self._n_simulations_mixed.value()
        s.alpha = self._alpha.value()
        s.seed = int(self._seed.value())
        s.max_failed_simulations = self._max_failed.value()
        s.parallel = self._parallel.currentData()
        cores_data = self._cores_mode.currentData()
        s.n_cores = self._n_cores.value() if cores_data == "custom" else cores_data
        s.scenario_configs = {}
        for name in self._scenario_spins:
            cfg = {
                key: spin.value() for key, spin in self._scenario_spins[name].items()
            }
            cfg.update(
                {
                    key: combo.currentData()
                    for key, combo in self._scenario_combos[name].items()
                }
            )
            s.scenario_configs[name] = cfg
        mode = ThemeMode(self._theme.currentData())
        save_theme_mode(mode)
        apply_theme(mode)
        save_font_size(self._font_size.value())
        apply_font_size(self._font_size.value())
        self.accept()
