"""Tests for AnalysisTab — common settings, power analysis, and sample size search."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from mcpower_gui.state import ModelState
from mcpower_gui.tabs.analysis_tab import AnalysisTab

_app = QApplication.instance() or QApplication([])


@pytest.fixture
def state():
    return ModelState()


@pytest.fixture
def tab(state):
    widget = AnalysisTab(state)
    yield widget
    widget.deleteLater()


# ---------------------------------------------------------------------------
# _gather_common_params: correction mapping
# ---------------------------------------------------------------------------


class TestGatherCommonParamsCorrection:
    """Tests for correction text-to-value mapping in _gather_common_params()."""

    def test_none_maps_to_empty_string(self, tab, state):
        """Correction 'None' maps to empty string."""
        state.model_type = "linear_regression"
        tab._correction.setCurrentText("None")
        params = tab._gather_common_params()
        assert params["correction"] == ""

    def test_tukey_hsd_maps_to_tukey(self, tab, state):
        """Correction 'Tukey HSD' maps to 'tukey'."""
        state.model_type = "anova"
        tab.set_model_type("anova")
        tab._correction.setCurrentText("Tukey HSD")
        params = tab._gather_common_params()
        assert params["correction"] == "tukey"

    def test_bonferroni_passes_through(self, tab, state):
        """Correction 'Bonferroni' passes through unchanged."""
        state.model_type = "linear_regression"
        tab._correction.setCurrentText("Bonferroni")
        params = tab._gather_common_params()
        assert params["correction"] == "Bonferroni"

    def test_holm_passes_through(self, tab, state):
        """Correction 'Holm' passes through unchanged."""
        state.model_type = "linear_regression"
        tab._correction.setCurrentText("Holm")
        params = tab._gather_common_params()
        assert params["correction"] == "Holm"

    def test_benjamini_hochberg_passes_through(self, tab, state):
        """Correction 'Benjamini-Hochberg' passes through unchanged."""
        state.model_type = "linear_regression"
        tab._correction.setCurrentText("Benjamini-Hochberg")
        params = tab._gather_common_params()
        assert params["correction"] == "Benjamini-Hochberg"


# ---------------------------------------------------------------------------
# _gather_common_params: ANOVA vs regression branching
# ---------------------------------------------------------------------------


class TestGatherCommonParamsAnovaBranch:
    """Tests for ANOVA mode branching in _gather_common_params()."""

    def test_anova_target_test_starts_with_overall(self, tab, state):
        """In ANOVA mode, target_test always begins with 'overall'."""
        state.model_type = "anova"
        params = tab._gather_common_params()
        assert params["target_test"].startswith("overall")

    def test_anova_test_formula_is_empty(self, tab, state):
        """In ANOVA mode, test_formula is always empty string."""
        state.model_type = "anova"
        tab._test_formula.setText("some formula")
        params = tab._gather_common_params()
        assert params["test_formula"] == ""

    def test_anova_no_post_hoc_returns_overall_only(self, tab, state):
        """In ANOVA mode with no post hoc selections, target_test is just 'overall'."""
        state.model_type = "anova"
        params = tab._gather_common_params()
        assert params["target_test"] == "overall"

    def test_anova_with_post_hoc_appends_comparisons(self, tab, state):
        """In ANOVA mode, selected post hoc comparisons are appended to 'overall'."""
        state.model_type = "anova"
        tab._post_hoc_selector.set_factors({"group": 3})
        # Check the first comparison
        tab._post_hoc_selector._checkboxes[0][1].setChecked(True)
        comparison_name = tab._post_hoc_selector._checkboxes[0][0]
        params = tab._gather_common_params()
        assert params["target_test"] == f"overall, {comparison_name}"

    def test_anova_with_all_post_hoc(self, tab, state):
        """In ANOVA mode, selecting all post hoc comparisons appends all to 'overall'."""
        state.model_type = "anova"
        tab._post_hoc_selector.set_factors({"group": 2})
        tab._post_hoc_selector._checkboxes[0][1].setChecked(True)
        comparison_name = tab._post_hoc_selector._checkboxes[0][0]
        params = tab._gather_common_params()
        expected = f"overall, {comparison_name}"
        assert params["target_test"] == expected

    def test_anova_includes_scenarios_key(self, tab, state):
        """ANOVA params include 'scenarios' key."""
        state.model_type = "anova"
        tab._scenarios.setChecked(True)
        params = tab._gather_common_params()
        assert params["scenarios"] is True

    def test_anova_includes_summary_key(self, tab, state):
        """ANOVA params include 'summary' key set to 'short'."""
        state.model_type = "anova"
        params = tab._gather_common_params()
        assert params["summary"] == "short"


class TestGatherCommonParamsRegressionBranch:
    """Tests for regression mode branching in _gather_common_params()."""

    def test_regression_uses_target_tests_selector(self, tab, state):
        """In regression mode, target_test comes from TargetTestSelector."""
        state.model_type = "linear_regression"
        tab._target_tests.set_tests(["x1", "x2"])
        params = tab._gather_common_params()
        # All selected by default = "all"
        assert params["target_test"] == "all"

    def test_regression_uses_test_formula_text(self, tab, state):
        """In regression mode, test_formula is taken from the text field."""
        state.model_type = "linear_regression"
        tab._test_formula.setText("  y ~ x1 + x2  ")
        params = tab._gather_common_params()
        assert params["test_formula"] == "y ~ x1 + x2"

    def test_regression_empty_test_formula(self, tab, state):
        """In regression mode, empty test_formula is empty string."""
        state.model_type = "linear_regression"
        tab._test_formula.setText("")
        params = tab._gather_common_params()
        assert params["test_formula"] == ""

    def test_regression_no_post_hoc_uses_base_target_only(self, tab, state):
        """Without post hoc selections, target_test equals base target only."""
        state.model_type = "linear_regression"
        tab._target_tests.set_tests(["x1", "x2"])
        # Uncheck x2 so we get a specific subset
        tab._target_tests._checkboxes[1][1].setChecked(False)
        params = tab._gather_common_params()
        assert params["target_test"] == "x1"

    def test_regression_with_post_hoc_appends_comparisons(self, tab, state):
        """In regression mode, post hoc comparisons are appended to base target."""
        state.model_type = "linear_regression"
        tab._target_tests.set_tests(["x1", "x2"])
        tab._post_hoc_selector.set_factors({"group": 2})
        tab._post_hoc_selector._checkboxes[0][1].setChecked(True)
        comparison_name = tab._post_hoc_selector._checkboxes[0][0]
        params = tab._gather_common_params()
        assert params["target_test"] == f"all, {comparison_name}"

    def test_regression_scenarios_unchecked_by_default(self, tab, state):
        """Scenarios checkbox is unchecked by default."""
        state.model_type = "linear_regression"
        params = tab._gather_common_params()
        assert params["scenarios"] is False

    def test_regression_scenarios_checked(self, tab, state):
        """Scenarios checkbox when checked returns True."""
        state.model_type = "linear_regression"
        tab._scenarios.setChecked(True)
        params = tab._gather_common_params()
        assert params["scenarios"] is True

    def test_regression_summary_always_short(self, tab, state):
        """Summary is always 'short' in regression mode."""
        state.model_type = "linear_regression"
        params = tab._gather_common_params()
        assert params["summary"] == "short"


# ---------------------------------------------------------------------------
# _gather_common_params: post hoc merging
# ---------------------------------------------------------------------------


class TestGatherCommonParamsPostHocMerging:
    """Tests for post hoc merging with target_test in both modes."""

    def test_anova_multiple_post_hoc(self, tab, state):
        """ANOVA mode with multiple post hoc selections joins them all."""
        state.model_type = "anova"
        tab._post_hoc_selector.set_factors({"group": 3})
        # Check first two comparisons
        tab._post_hoc_selector._checkboxes[0][1].setChecked(True)
        tab._post_hoc_selector._checkboxes[1][1].setChecked(True)
        name0 = tab._post_hoc_selector._checkboxes[0][0]
        name1 = tab._post_hoc_selector._checkboxes[1][0]
        params = tab._gather_common_params()
        assert params["target_test"] == f"overall, {name0}, {name1}"

    def test_regression_multiple_post_hoc(self, tab, state):
        """Regression mode with multiple post hoc selections appends them all."""
        state.model_type = "linear_regression"
        tab._target_tests.set_tests(["x1"])
        tab._post_hoc_selector.set_factors({"group": 2, "cond": 2})
        # Check one from each factor
        tab._post_hoc_selector._checkboxes[0][1].setChecked(True)
        tab._post_hoc_selector._checkboxes[1][1].setChecked(True)
        name0 = tab._post_hoc_selector._checkboxes[0][0]
        name1 = tab._post_hoc_selector._checkboxes[1][0]
        params = tab._gather_common_params()
        assert params["target_test"] == f"all, {name0}, {name1}"

    def test_empty_post_hoc_no_trailing_comma(self, tab, state):
        """When post hoc is empty, there is no trailing comma in target_test."""
        state.model_type = "linear_regression"
        tab._target_tests.set_tests(["x1", "x2"])
        params = tab._gather_common_params()
        assert ", ," not in params["target_test"]
        assert not params["target_test"].endswith(",")


# ---------------------------------------------------------------------------
# set_model_type: Tukey HSD add/remove
# ---------------------------------------------------------------------------


class TestSetModelTypeTukey:
    """Tests for Tukey HSD availability based on model type."""

    def test_anova_adds_tukey_hsd(self, tab):
        """Setting model type to anova adds 'Tukey HSD' to correction combo."""
        tab.set_model_type("anova")
        idx = tab._correction.findText("Tukey HSD")
        assert idx != -1

    def test_regression_removes_tukey_hsd(self, tab):
        """Setting model type to regression removes 'Tukey HSD' from correction combo."""
        tab.set_model_type("anova")  # Add it first
        tab.set_model_type("linear_regression")  # Then remove
        idx = tab._correction.findText("Tukey HSD")
        assert idx == -1

    def test_regression_no_duplicate_tukey_add(self, tab):
        """Calling set_model_type('anova') twice does not add duplicate Tukey HSD."""
        tab.set_model_type("anova")
        tab.set_model_type("anova")
        count = sum(
            1
            for i in range(tab._correction.count())
            if tab._correction.itemText(i) == "Tukey HSD"
        )
        assert count == 1

    def test_removing_tukey_resets_selection_if_selected(self, tab):
        """If Tukey HSD was selected and removed, correction resets to 'None'."""
        tab.set_model_type("anova")
        tab._correction.setCurrentText("Tukey HSD")
        tab.set_model_type("linear_regression")
        assert tab._correction.currentText() == "None"

    def test_removing_tukey_preserves_other_selection(self, tab):
        """If a non-Tukey correction was selected, switching away from anova preserves it."""
        tab.set_model_type("anova")
        tab._correction.setCurrentText("Bonferroni")
        tab.set_model_type("linear_regression")
        assert tab._correction.currentText() == "Bonferroni"

    def test_initial_correction_items_no_tukey(self, tab):
        """Initially (before set_model_type), Tukey HSD is not in the combo."""
        idx = tab._correction.findText("Tukey HSD")
        assert idx == -1

    def test_initial_correction_items(self, tab):
        """Initial correction combo has None, Bonferroni, Benjamini-Hochberg, Holm."""
        items = [tab._correction.itemText(i) for i in range(tab._correction.count())]
        assert items == ["None", "Bonferroni", "Benjamini-Hochberg", "Holm"]


# ---------------------------------------------------------------------------
# set_model_type: target_tests / test_formula visibility
# ---------------------------------------------------------------------------


class TestSetModelTypeVisibility:
    """Tests for target_tests and test_formula visibility based on model type."""

    def test_anova_hides_target_tests(self, tab):
        """ANOVA mode hides the target tests label and selector."""
        tab.set_model_type("anova")
        assert tab._target_tests_label.isHidden()
        assert tab._target_tests.isHidden()

    def test_anova_hides_test_formula(self, tab):
        """ANOVA mode hides the test formula label and field."""
        tab.set_model_type("anova")
        assert tab._test_formula_label.isHidden()
        assert tab._test_formula.isHidden()

    def test_regression_shows_target_tests(self, tab):
        """Regression mode shows the target tests label and selector."""
        tab.set_model_type("anova")  # Hide first
        tab.set_model_type("linear_regression")  # Then show
        assert not tab._target_tests_label.isHidden()
        assert not tab._target_tests.isHidden()

    def test_regression_shows_test_formula(self, tab):
        """Regression mode shows the test formula label and field."""
        tab.set_model_type("anova")  # Hide first
        tab.set_model_type("linear_regression")  # Then show
        assert not tab._test_formula_label.isHidden()
        assert not tab._test_formula.isHidden()

    def test_correction_enabled_in_anova(self, tab):
        """Correction combo is enabled in ANOVA mode."""
        tab.set_model_type("anova")
        assert tab._correction.isEnabled()
        assert tab._correction_label.isEnabled()

    def test_correction_enabled_in_regression(self, tab):
        """Correction combo is enabled in regression mode."""
        tab.set_model_type("linear_regression")
        assert tab._correction.isEnabled()
        assert tab._correction_label.isEnabled()


# ---------------------------------------------------------------------------
# restore_params: combo restoration
# ---------------------------------------------------------------------------


class TestRestoreParamsCorrection:
    """Tests for correction combo restoration in restore_params()."""

    def test_empty_correction_sets_none(self, tab, state):
        """Empty correction string restores combo to 'None'."""
        tab._correction.setCurrentText("Bonferroni")
        tab.restore_params({"correction": ""})
        assert tab._correction.currentText() == "None"

    def test_missing_correction_sets_none(self, tab, state):
        """Missing correction key restores combo to 'None' (default empty)."""
        tab._correction.setCurrentText("Bonferroni")
        tab.restore_params({})
        assert tab._correction.currentText() == "None"

    def test_tukey_correction_sets_tukey_hsd(self, tab, state):
        """Correction 'tukey' restores combo to 'Tukey HSD'."""
        state.model_type = "anova"
        tab.set_model_type("anova")  # Make Tukey HSD available
        tab.restore_params({"correction": "tukey"})
        assert tab._correction.currentText() == "Tukey HSD"

    def test_case_insensitive_match(self, tab, state):
        """Correction 'bonferroni' (lowercase) matches 'Bonferroni'."""
        tab.restore_params({"correction": "bonferroni"})
        assert tab._correction.currentText() == "Bonferroni"

    def test_case_insensitive_match_holm(self, tab, state):
        """Correction 'holm' (lowercase) matches 'Holm'."""
        tab.restore_params({"correction": "holm"})
        assert tab._correction.currentText() == "Holm"

    def test_case_insensitive_match_mixed_case(self, tab, state):
        """Correction 'BENJAMINI-HOCHBERG' (uppercase) matches 'Benjamini-Hochberg'."""
        tab.restore_params({"correction": "BENJAMINI-HOCHBERG"})
        assert tab._correction.currentText() == "Benjamini-Hochberg"

    def test_tukey_case_insensitive(self, tab, state):
        """Correction 'TUKEY' maps to 'Tukey HSD'."""
        state.model_type = "anova"
        tab.set_model_type("anova")
        tab.restore_params({"correction": "TUKEY"})
        assert tab._correction.currentText() == "Tukey HSD"


# ---------------------------------------------------------------------------
# restore_params: None checks for optional fields
# ---------------------------------------------------------------------------


class TestRestoreParamsOptionalFields:
    """Tests for None-guarded optional field restoration."""

    def test_target_power_restored_when_present(self, tab, state):
        """target_power is set when present in params."""
        tab.restore_params({"target_power": 95.0})
        assert tab._target_power.value() == 95.0

    def test_target_power_not_changed_when_none(self, tab, state):
        """target_power stays at default when key is absent."""
        original = tab._target_power.value()
        tab.restore_params({})
        assert tab._target_power.value() == original

    def test_sample_size_restored_when_present(self, tab, state):
        """sample_size is set when present in params."""
        tab.restore_params({"sample_size": 500})
        assert tab._power_sample_size.value() == 500

    def test_sample_size_not_changed_when_none(self, tab, state):
        """sample_size stays at default (100) when key is absent."""
        tab.restore_params({})
        assert tab._power_sample_size.value() == 100

    def test_ss_from_restored_when_present(self, tab, state):
        """ss_from is set when present in params."""
        tab.restore_params({"ss_from": 50})
        assert tab._ss_from.value() == 50

    def test_ss_from_not_changed_when_none(self, tab, state):
        """ss_from stays at default (30) when key is absent."""
        tab.restore_params({})
        assert tab._ss_from.value() == 30

    def test_ss_to_restored_when_present(self, tab, state):
        """ss_to is set when present in params."""
        tab.restore_params({"ss_to": 500})
        assert tab._ss_to.value() == 500

    def test_ss_to_not_changed_when_none(self, tab, state):
        """ss_to stays at default (200) when key is absent."""
        tab.restore_params({})
        assert tab._ss_to.value() == 200

    def test_ss_by_restored_when_present(self, tab, state):
        """ss_by is set when present in params."""
        tab.restore_params({"ss_by": 25})
        assert tab._ss_by.value() == 25

    def test_ss_by_not_changed_when_none(self, tab, state):
        """ss_by stays at default (10) when key is absent."""
        tab.restore_params({})
        assert tab._ss_by.value() == 10


# ---------------------------------------------------------------------------
# restore_params: scenarios and test_formula
# ---------------------------------------------------------------------------


class TestRestoreParamsOtherFields:
    """Tests for scenarios checkbox and test_formula restoration."""

    def test_scenarios_restored_true(self, tab, state):
        """scenarios=True checks the scenarios checkbox."""
        tab.restore_params({"scenarios": True})
        assert tab._scenarios.isChecked() is True

    def test_scenarios_restored_false(self, tab, state):
        """scenarios=False unchecks the scenarios checkbox."""
        tab._scenarios.setChecked(True)
        tab.restore_params({"scenarios": False})
        assert tab._scenarios.isChecked() is False

    def test_scenarios_defaults_to_false(self, tab, state):
        """Missing 'scenarios' key defaults to False."""
        tab._scenarios.setChecked(True)
        tab.restore_params({})
        assert tab._scenarios.isChecked() is False

    def test_test_formula_restored(self, tab, state):
        """test_formula string is set in the line edit."""
        tab.restore_params({"test_formula": "y ~ x1"})
        assert tab._test_formula.text() == "y ~ x1"

    def test_test_formula_defaults_to_empty(self, tab, state):
        """Missing 'test_formula' key defaults to empty string."""
        tab._test_formula.setText("old formula")
        tab.restore_params({})
        assert tab._test_formula.text() == ""

    def test_restore_calls_set_model_type(self, tab, state):
        """restore_params() calls set_model_type() at the end to apply constraints."""
        state.model_type = "anova"
        tab.restore_params({"correction": "tukey"})
        # After restore_params, ANOVA constraints should be applied:
        # target_tests should be hidden
        assert tab._target_tests_label.isHidden()
        assert tab._target_tests.isHidden()


# ---------------------------------------------------------------------------
# restore_params: full roundtrip
# ---------------------------------------------------------------------------


class TestRestoreParamsRoundtrip:
    """Tests for full parameter roundtrip through gather and restore."""

    def test_full_params_restore(self, tab, state):
        """All parameters are restored correctly in a single call."""
        state.model_type = "linear_regression"
        tab.set_model_type("linear_regression")
        tab.restore_params(
            {
                "correction": "bonferroni",
                "scenarios": True,
                "test_formula": "y ~ x1 + x2",
                "target_power": 90.0,
                "sample_size": 250,
                "ss_from": 40,
                "ss_to": 300,
                "ss_by": 20,
            }
        )
        assert tab._correction.currentText() == "Bonferroni"
        assert tab._scenarios.isChecked() is True
        assert tab._test_formula.text() == "y ~ x1 + x2"
        assert tab._target_power.value() == 90.0
        assert tab._power_sample_size.value() == 250
        assert tab._ss_from.value() == 40
        assert tab._ss_to.value() == 300
        assert tab._ss_by.value() == 20


# ---------------------------------------------------------------------------
# _on_run_power: signal emission
# ---------------------------------------------------------------------------


class TestOnRunPower:
    """Tests for _on_run_power() signal emission with correct parameters."""

    def test_emits_run_power_requested(self, tab, state):
        """Calling _on_run_power emits run_power_requested signal."""
        results = []
        tab.run_power_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._on_run_power()
        assert len(results) == 1

    def test_params_include_sample_size(self, tab, state):
        """Emitted params include sample_size from the spin box."""
        results = []
        tab.run_power_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._power_sample_size.setValue(200)
        tab._on_run_power()
        assert results[0]["sample_size"] == 200

    def test_params_include_common_params(self, tab, state):
        """Emitted params include all common analysis parameters."""
        results = []
        tab.run_power_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._scenarios.setChecked(True)
        tab._correction.setCurrentText("Bonferroni")
        tab._on_run_power()
        params = results[0]
        assert params["scenarios"] is True
        assert params["correction"] == "Bonferroni"
        assert params["summary"] == "short"
        assert "target_test" in params
        assert "test_formula" in params

    def test_updates_state_target_power(self, tab, state):
        """_on_run_power updates state.target_power from the spin box."""
        tab._target_power.setValue(90.0)
        state.model_type = "linear_regression"
        results = []
        tab.run_power_requested.connect(lambda d: results.append(d))
        tab._on_run_power()
        assert state.target_power == 90.0

    def test_custom_sample_size_value(self, tab, state):
        """Custom sample size values are emitted correctly."""
        results = []
        tab.run_power_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._power_sample_size.setValue(1000)
        tab._on_run_power()
        assert results[0]["sample_size"] == 1000


# ---------------------------------------------------------------------------
# _on_run_sample_size: validation (from >= to)
# ---------------------------------------------------------------------------


class TestOnRunSampleSizeValidationFromTo:
    """Tests for from >= to validation in _on_run_sample_size()."""

    def test_from_equals_to_shows_warning(self, tab, state):
        """When from == to, a warning is shown and no signal is emitted."""
        results = []
        tab.run_sample_size_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._ss_from.setValue(100)
        tab._ss_to.setValue(100)
        with patch("mcpower_gui.tabs.analysis_tab.QMessageBox.warning"):
            tab._on_run_sample_size()
        assert len(results) == 0

    def test_from_greater_than_to_shows_warning(self, tab, state):
        """When from > to, a warning is shown and no signal is emitted."""
        results = []
        tab.run_sample_size_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._ss_from.setValue(200)
        tab._ss_to.setValue(100)
        with patch("mcpower_gui.tabs.analysis_tab.QMessageBox.warning"):
            tab._on_run_sample_size()
        assert len(results) == 0

    def test_from_less_than_to_emits_signal(self, tab, state):
        """When from < to, the signal is emitted."""
        results = []
        tab.run_sample_size_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._ss_from.setValue(30)
        tab._ss_to.setValue(200)
        tab._ss_by.setValue(10)
        tab._on_run_sample_size()
        assert len(results) == 1

    def test_warning_called_with_correct_args_from_ge_to(self, tab, state):
        """Warning message includes the from and to values."""
        state.model_type = "linear_regression"
        tab._ss_from.setValue(150)
        tab._ss_to.setValue(100)
        with patch("mcpower_gui.tabs.analysis_tab.QMessageBox.warning") as mock_warn:
            tab._on_run_sample_size()
            mock_warn.assert_called_once()
            args = mock_warn.call_args
            assert "150" in str(args)
            assert "100" in str(args)


# ---------------------------------------------------------------------------
# _on_run_sample_size: validation (step > range)
# ---------------------------------------------------------------------------


class TestOnRunSampleSizeValidationStep:
    """Tests for step > range validation in _on_run_sample_size()."""

    def test_step_larger_than_range_shows_warning(self, tab, state):
        """When step > (to - from), a warning is shown and no signal emitted."""
        results = []
        tab.run_sample_size_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._ss_from.setValue(30)
        tab._ss_to.setValue(50)
        tab._ss_by.setValue(30)  # step 30 > range 20
        with patch("mcpower_gui.tabs.analysis_tab.QMessageBox.warning"):
            tab._on_run_sample_size()
        assert len(results) == 0

    def test_step_equals_range_emits_signal(self, tab, state):
        """When step == (to - from), the signal is emitted (valid edge case)."""
        results = []
        tab.run_sample_size_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._ss_from.setValue(30)
        tab._ss_to.setValue(50)
        tab._ss_by.setValue(20)  # step 20 == range 20
        tab._on_run_sample_size()
        assert len(results) == 1

    def test_step_less_than_range_emits_signal(self, tab, state):
        """When step < (to - from), the signal is emitted."""
        results = []
        tab.run_sample_size_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._ss_from.setValue(30)
        tab._ss_to.setValue(200)
        tab._ss_by.setValue(10)
        tab._on_run_sample_size()
        assert len(results) == 1

    def test_warning_called_with_correct_args_step(self, tab, state):
        """Warning message includes the step and range values."""
        state.model_type = "linear_regression"
        tab._ss_from.setValue(30)
        tab._ss_to.setValue(50)
        tab._ss_by.setValue(25)
        with patch("mcpower_gui.tabs.analysis_tab.QMessageBox.warning") as mock_warn:
            tab._on_run_sample_size()
            mock_warn.assert_called_once()
            args = mock_warn.call_args
            assert "25" in str(args)  # step
            assert "20" in str(args)  # range


# ---------------------------------------------------------------------------
# _on_run_sample_size: signal emission with ss_from/to/by
# ---------------------------------------------------------------------------


class TestOnRunSampleSizeSignal:
    """Tests for _on_run_sample_size() signal emission with correct parameters."""

    def test_emits_run_sample_size_requested(self, tab, state):
        """Calling _on_run_sample_size emits run_sample_size_requested signal."""
        results = []
        tab.run_sample_size_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._ss_from.setValue(30)
        tab._ss_to.setValue(200)
        tab._ss_by.setValue(10)
        tab._on_run_sample_size()
        assert len(results) == 1

    def test_params_include_ss_from_to_by(self, tab, state):
        """Emitted params include ss_from, ss_to, and ss_by."""
        results = []
        tab.run_sample_size_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._ss_from.setValue(40)
        tab._ss_to.setValue(300)
        tab._ss_by.setValue(20)
        tab._on_run_sample_size()
        params = results[0]
        assert params["ss_from"] == 40
        assert params["ss_to"] == 300
        assert params["ss_by"] == 20

    def test_params_include_common_params(self, tab, state):
        """Emitted params include all common analysis parameters."""
        results = []
        tab.run_sample_size_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._scenarios.setChecked(True)
        tab._correction.setCurrentText("Holm")
        tab._ss_from.setValue(30)
        tab._ss_to.setValue(200)
        tab._ss_by.setValue(10)
        tab._on_run_sample_size()
        params = results[0]
        assert params["scenarios"] is True
        assert params["correction"] == "Holm"
        assert params["summary"] == "short"

    def test_updates_state_target_power(self, tab, state):
        """_on_run_sample_size updates state.target_power from the spin box."""
        tab._target_power.setValue(85.0)
        state.model_type = "linear_regression"
        results = []
        tab.run_sample_size_requested.connect(lambda d: results.append(d))
        tab._ss_from.setValue(30)
        tab._ss_to.setValue(200)
        tab._ss_by.setValue(10)
        tab._on_run_sample_size()
        assert state.target_power == 85.0

    def test_no_sample_size_key_in_sample_size_signal(self, tab, state):
        """run_sample_size_requested params should not have 'sample_size' key."""
        results = []
        tab.run_sample_size_requested.connect(lambda d: results.append(d))
        state.model_type = "linear_regression"
        tab._ss_from.setValue(30)
        tab._ss_to.setValue(200)
        tab._ss_by.setValue(10)
        tab._on_run_sample_size()
        assert "sample_size" not in results[0]


# ---------------------------------------------------------------------------
# set_model_ready: button enable/disable
# ---------------------------------------------------------------------------


class TestSetModelReady:
    """Tests for set_model_ready() button enable/disable behavior."""

    def test_buttons_disabled_initially(self, tab):
        """Both run buttons are disabled when the tab is created."""
        assert not tab._btn_power.isEnabled()
        assert not tab._btn_ss.isEnabled()

    def test_buttons_enabled_when_ready(self, tab):
        """Both run buttons are enabled when set_model_ready(True)."""
        tab.set_model_ready(True)
        assert tab._btn_power.isEnabled()
        assert tab._btn_ss.isEnabled()

    def test_buttons_disabled_when_not_ready(self, tab):
        """Both run buttons are disabled when set_model_ready(False)."""
        tab.set_model_ready(True)
        tab.set_model_ready(False)
        assert not tab._btn_power.isEnabled()
        assert not tab._btn_ss.isEnabled()

    def test_model_ready_flag_stored(self, tab):
        """set_model_ready stores the flag internally for use by set_running."""
        tab.set_model_ready(True)
        assert tab._model_ready is True
        tab.set_model_ready(False)
        assert tab._model_ready is False

    def test_placeholder_updated_with_formula(self, tab, state):
        """When formula is set, placeholder text includes the formula."""
        state.formula = "y ~ x1 + x2"
        tab.set_model_ready(True)
        placeholder = tab._test_formula.placeholderText()
        assert "y ~ x1 + x2" in placeholder

    def test_placeholder_default_without_formula(self, tab, state):
        """When formula is empty, placeholder is the default text."""
        state.formula = ""
        tab.set_model_ready(True)
        placeholder = tab._test_formula.placeholderText()
        assert placeholder == "Leave empty to use model formula"


# ---------------------------------------------------------------------------
# set_running: button enable/disable
# ---------------------------------------------------------------------------


class TestSetRunning:
    """Tests for set_running() button enable/disable behavior."""

    def test_buttons_disabled_when_running(self, tab):
        """Both run buttons are disabled when set_running(True)."""
        tab.set_model_ready(True)
        tab.set_running(True)
        assert not tab._btn_power.isEnabled()
        assert not tab._btn_ss.isEnabled()

    def test_buttons_re_enabled_when_not_running_and_model_ready(self, tab):
        """Buttons are re-enabled when set_running(False) and model is ready."""
        tab.set_model_ready(True)
        tab.set_running(True)
        tab.set_running(False)
        assert tab._btn_power.isEnabled()
        assert tab._btn_ss.isEnabled()

    def test_buttons_stay_disabled_when_not_running_and_model_not_ready(self, tab):
        """Buttons stay disabled when set_running(False) but model is not ready."""
        tab.set_model_ready(False)
        tab.set_running(True)
        tab.set_running(False)
        assert not tab._btn_power.isEnabled()
        assert not tab._btn_ss.isEnabled()

    def test_running_then_ready_interaction(self, tab):
        """set_running respects the _model_ready flag correctly."""
        # Model not ready, not running
        tab.set_model_ready(False)
        tab.set_running(False)
        assert not tab._btn_power.isEnabled()

        # Model ready, not running
        tab.set_model_ready(True)
        tab.set_running(False)
        assert tab._btn_power.isEnabled()

        # Model ready, running
        tab.set_running(True)
        assert not tab._btn_power.isEnabled()

        # Model ready, stopped
        tab.set_running(False)
        assert tab._btn_power.isEnabled()


# ---------------------------------------------------------------------------
# Initial widget state
# ---------------------------------------------------------------------------


class TestInitialState:
    """Tests for initial widget state on construction."""

    def test_initial_target_power(self, tab, state):
        """Target power spin box initialized from state.target_power."""
        assert tab._target_power.value() == state.target_power

    def test_initial_scenarios_unchecked(self, tab):
        """Scenarios checkbox is unchecked initially."""
        assert not tab._scenarios.isChecked()

    def test_initial_correction_is_none(self, tab):
        """Initial correction selection is 'None'."""
        assert tab._correction.currentText() == "None"

    def test_initial_power_sample_size(self, tab):
        """Power sample size spin box initialized to 100."""
        assert tab._power_sample_size.value() == 100

    def test_initial_ss_from(self, tab):
        """Sample size 'from' spin box initialized to 30."""
        assert tab._ss_from.value() == 30

    def test_initial_ss_to(self, tab):
        """Sample size 'to' spin box initialized to 200."""
        assert tab._ss_to.value() == 200

    def test_initial_ss_by(self, tab):
        """Sample size 'step' spin box initialized to 10."""
        assert tab._ss_by.value() == 10

    def test_initial_test_formula_empty(self, tab):
        """Test formula line edit is empty initially."""
        assert tab._test_formula.text() == ""

    def test_post_hoc_group_hidden_initially(self, tab):
        """Post hoc group is hidden initially."""
        assert tab._post_hoc_group.isHidden()

    def test_signals_defined(self, tab):
        """Both run signals are defined on the widget."""
        assert hasattr(tab, "run_power_requested")
        assert hasattr(tab, "run_sample_size_requested")


# ---------------------------------------------------------------------------
# _parse_test_formula: static method
# ---------------------------------------------------------------------------


class TestParseTestFormula:
    """Tests for _parse_test_formula() parsing logic."""

    def test_simple_main_effects(self):
        """Parses 'y ~ x1 + x2' into main effects {x1, x2}."""
        main, interactions = AnalysisTab._parse_test_formula("y ~ x1 + x2")
        assert main == {"x1", "x2"}
        assert interactions == []

    def test_star_expansion(self):
        """Parses 'y ~ a*b' into main effects {a, b} and interaction [{a, b}]."""
        main, interactions = AnalysisTab._parse_test_formula("y ~ a*b")
        assert main == {"a", "b"}
        assert interactions == [frozenset({"a", "b"})]

    def test_triple_star_expansion(self):
        """Parses 'y ~ a*b*c' into 3 main effects and 3 pairwise interactions."""
        main, interactions = AnalysisTab._parse_test_formula("y ~ a*b*c")
        assert main == {"a", "b", "c"}
        assert len(interactions) == 3
        assert frozenset({"a", "b"}) in interactions
        assert frozenset({"a", "c"}) in interactions
        assert frozenset({"b", "c"}) in interactions

    def test_explicit_interaction(self):
        """Parses 'y ~ x1:x2' into interaction without adding main effects."""
        main, interactions = AnalysisTab._parse_test_formula("y ~ x1:x2")
        assert main == set()
        assert interactions == [frozenset({"x1", "x2"})]

    def test_mixed_terms(self):
        """Parses 'y ~ x1 + x2:x3' into main effect + interaction."""
        main, interactions = AnalysisTab._parse_test_formula("y ~ x1 + x2:x3")
        assert main == {"x1"}
        assert interactions == [frozenset({"x2", "x3"})]

    def test_random_effects_stripped(self):
        """Parses 'y ~ x1 + (1|school)' stripping random effects."""
        main, interactions = AnalysisTab._parse_test_formula("y ~ x1 + (1|school)")
        assert main == {"x1"}
        assert interactions == []

    def test_equals_separator(self):
        """Parses 'y = x1 + x2' with = separator."""
        main, interactions = AnalysisTab._parse_test_formula("y = x1 + x2")
        assert main == {"x1", "x2"}

    def test_empty_formula(self):
        """Empty formula returns empty sets."""
        main, interactions = AnalysisTab._parse_test_formula("")
        assert main == set()
        assert interactions == []

    def test_whitespace_handling(self):
        """Handles extra whitespace gracefully."""
        main, interactions = AnalysisTab._parse_test_formula("  y ~  x1  +  x2  ")
        assert main == {"x1", "x2"}
