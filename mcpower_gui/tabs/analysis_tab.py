"""Analysis tab — common settings, power analysis, and sample size search."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui.state import ModelState
from mcpower_gui.widgets.info_button import attach_info_button
from mcpower_gui.widgets.post_hoc_selector import PostHocSelector
from mcpower_gui.widgets.target_test_selector import TargetTestSelector


class AnalysisTab(QWidget):
    """Common analysis settings (deduplicated) + Find Power / Find Sample Size groups.

    Emits run signals with a dict of all per-run parameters.
    """

    run_power_requested = Signal(dict)
    run_sample_size_requested = Signal(dict)

    def __init__(self, state: ModelState, parent=None):
        super().__init__(parent)
        self._state = state
        self._model_ready = False

        root = QVBoxLayout(self)

        # ── Common Analysis Settings ─────────────────────────
        common_group = QGroupBox("Common Analysis Settings")
        cf = QFormLayout(common_group)

        self._target_power = QDoubleSpinBox()
        self._target_power.setRange(1.0, 99.99)
        self._target_power.setValue(state.target_power)
        self._target_power.setSingleStep(5.0)
        self._target_power.setDecimals(1)
        cf.addRow("Target power (%):", self._target_power)

        self._scenarios = QCheckBox()
        cf.addRow("Scenarios:", self._scenarios)

        self._correction = QComboBox()
        self._correction.addItems(["None", "Bonferroni", "Benjamini-Hochberg", "Holm"])
        self._correction_label = QLabel("Correction:")
        cf.addRow(self._correction_label, self._correction)

        self._target_tests = TargetTestSelector()
        self._target_tests_label = QLabel("Target tests:")
        cf.addRow(self._target_tests_label, self._target_tests)

        self._test_formula = QLineEdit()
        self._test_formula.setPlaceholderText("Leave empty to use model formula")
        self._test_formula_label = QLabel("Test formula:")
        cf.addRow(self._test_formula_label, self._test_formula)

        root.addWidget(common_group)
        attach_info_button(
            common_group, "analysis_tab.md", "Common Analysis Settings", "Analysis Tab"
        )

        # ── Post Hoc Pairwise Comparisons ─────────────────────
        self._post_hoc_group = QGroupBox("Post Hoc Pairwise Comparisons")
        ph_layout = QVBoxLayout(self._post_hoc_group)
        self._post_hoc_selector = PostHocSelector()
        ph_layout.addWidget(self._post_hoc_selector)
        self._post_hoc_group.hide()
        root.addWidget(self._post_hoc_group)
        attach_info_button(
            self._post_hoc_group,
            "analysis_tab.md",
            "Post Hoc Pairwise Comparisons",
            "Analysis Tab",
        )

        # ── Find Power ───────────────────────────────────────
        power_group = QGroupBox("Find Power")
        pf = QFormLayout(power_group)

        self._power_sample_size = QSpinBox()
        self._power_sample_size.setRange(20, 100_000)
        self._power_sample_size.setValue(100)
        self._power_sample_size.setSingleStep(10)
        pf.addRow("Sample size:", self._power_sample_size)

        self._btn_power = QPushButton("Run Power Analysis")
        self._btn_power.setEnabled(False)
        pf.addRow(self._btn_power)

        root.addWidget(power_group)
        attach_info_button(power_group, "analysis_tab.md", "Find Power", "Analysis Tab")

        # ── Find Sample Size ─────────────────────────────────
        ss_group = QGroupBox("Find Sample Size")
        sf = QFormLayout(ss_group)

        self._ss_from = QSpinBox()
        self._ss_from.setRange(20, 100_000)
        self._ss_from.setValue(30)
        self._ss_from.setSingleStep(10)
        sf.addRow("From:", self._ss_from)

        self._ss_to = QSpinBox()
        self._ss_to.setRange(20, 100_000)
        self._ss_to.setValue(200)
        self._ss_to.setSingleStep(10)
        sf.addRow("To:", self._ss_to)

        self._ss_by = QSpinBox()
        self._ss_by.setRange(1, 1000)
        self._ss_by.setValue(10)
        sf.addRow("Step:", self._ss_by)

        self._btn_ss = QPushButton("Find Sample Size")
        self._btn_ss.setEnabled(False)
        sf.addRow(self._btn_ss)

        root.addWidget(ss_group)
        attach_info_button(
            ss_group, "analysis_tab.md", "Find Sample Size", "Analysis Tab"
        )

        root.addStretch()

        # Connections
        self._btn_power.clicked.connect(self._on_run_power)
        self._btn_ss.clicked.connect(self._on_run_sample_size)

    # ── Public API ───────────────────────────────────────────

    def set_model_type(self, model_type: str):
        """Enforce ANOVA constraints on target tests/test formula.

        Tukey HSD is only available in ANOVA mode.
        """
        is_anova = model_type == "anova"
        self._correction.setEnabled(True)
        self._correction_label.setEnabled(True)

        # Add/remove Tukey HSD based on model type
        tukey_idx = self._correction.findText("Tukey HSD")
        if is_anova:
            if tukey_idx == -1:
                self._correction.addItem("Tukey HSD")
            self._target_tests_label.hide()
            self._target_tests.hide()
            self._test_formula_label.hide()
            self._test_formula.hide()
        else:
            if tukey_idx != -1:
                # Reset to "None" if Tukey was selected before removing
                if self._correction.currentIndex() == tukey_idx:
                    self._correction.setCurrentIndex(0)
                self._correction.removeItem(tukey_idx)
            self._target_tests_label.show()
            self._target_tests.show()
            self._test_formula_label.show()
            self._test_formula.show()

    def set_available_tests(self, tests: list[str]):
        """Rebuild the target test checklist with *tests*."""
        self._target_tests.set_tests(tests)

    def set_available_factors(self, factors: dict[str, int]):
        """Update post hoc selector with current factor variables."""
        self._post_hoc_selector.set_factors(factors)
        if self._post_hoc_selector.has_any_factors():
            self._post_hoc_group.show()
        else:
            self._post_hoc_group.hide()

    def set_model_ready(self, ready: bool):
        """Enable/disable run buttons based on model readiness."""
        self._model_ready = ready
        self._btn_power.setEnabled(ready)
        self._btn_ss.setEnabled(ready)
        formula = self._state.formula
        if formula:
            self._test_formula.setPlaceholderText(
                f"Leave empty to use model formula: {formula}"
            )
        else:
            self._test_formula.setPlaceholderText("Leave empty to use model formula")

    def set_running(self, running: bool):
        """Disable/enable buttons while analysis is in progress."""
        self._btn_power.setEnabled(not running and self._model_ready)
        self._btn_ss.setEnabled(not running and self._model_ready)

    # ── Internal ─────────────────────────────────────────────

    def _gather_common_params(self) -> dict:
        """Read shared widgets into a parameter dict."""
        correction_text = self._correction.currentText()
        if correction_text == "Tukey HSD":
            correction = "tukey"
        elif correction_text == "None":
            correction = ""
        else:
            correction = correction_text

        post_hoc = self._post_hoc_selector.get_selected()

        if self._state.model_type == "anova":
            # ANOVA: base target is "overall", append post hoc selections
            parts = ["overall"]
            parts.extend(post_hoc)
            target_test = ", ".join(parts)
            return {
                "scenarios": self._scenarios.isChecked(),
                "summary": "short",
                "correction": correction,
                "target_test": target_test,
                "test_formula": "",
            }

        # Linear regression: use target test selector + append post hoc
        base_target = self._target_tests.get_value()
        if post_hoc:
            target_test = base_target + ", " + ", ".join(post_hoc)
        else:
            target_test = base_target
        return {
            "scenarios": self._scenarios.isChecked(),
            "summary": "short",
            "correction": correction,
            "target_test": target_test,
            "test_formula": self._test_formula.text().strip(),
        }

    def _on_run_power(self):
        self._state.target_power = self._target_power.value()
        params = self._gather_common_params()
        params["sample_size"] = self._power_sample_size.value()
        self.run_power_requested.emit(params)

    def _on_run_sample_size(self):
        ss_from = self._ss_from.value()
        ss_to = self._ss_to.value()
        ss_by = self._ss_by.value()

        if ss_from >= ss_to:
            QMessageBox.warning(
                self,
                "Invalid Range",
                f'"From" ({ss_from}) must be less than "To" ({ss_to}).',
            )
            return
        if ss_by > (ss_to - ss_from):
            QMessageBox.warning(
                self,
                "Invalid Step",
                f"Step ({ss_by}) is larger than the range ({ss_to - ss_from}).",
            )
            return

        self._state.target_power = self._target_power.value()
        params = self._gather_common_params()
        params["ss_from"] = ss_from
        params["ss_to"] = ss_to
        params["ss_by"] = ss_by
        self.run_sample_size_requested.emit(params)

    def restore_params(self, analysis_params: dict):
        """Restore analysis tab widgets from a history record's analysis_params."""
        # Correction combo
        correction = analysis_params.get("correction", "")
        if not correction:
            self._correction.setCurrentText("None")
        elif correction.lower() == "tukey":
            self._correction.setCurrentText("Tukey HSD")
        else:
            # Try case-insensitive match
            for i in range(self._correction.count()):
                if self._correction.itemText(i).lower() == correction.lower():
                    self._correction.setCurrentIndex(i)
                    break

        # Scenarios checkbox
        self._scenarios.setChecked(analysis_params.get("scenarios", False))

        # Test formula
        self._test_formula.setText(analysis_params.get("test_formula", ""))

        # Target power
        tp = analysis_params.get("target_power")
        if tp is not None:
            self._target_power.setValue(tp)

        # Power sample size
        ss = analysis_params.get("sample_size")
        if ss is not None:
            self._power_sample_size.setValue(ss)

        # Sample size search range
        ss_from = analysis_params.get("ss_from")
        if ss_from is not None:
            self._ss_from.setValue(ss_from)
        ss_to = analysis_params.get("ss_to")
        if ss_to is not None:
            self._ss_to.setValue(ss_to)
        ss_by = analysis_params.get("ss_by")
        if ss_by is not None:
            self._ss_by.setValue(ss_by)

        # Apply model type constraints
        self.set_model_type(self._state.model_type)
