"""Tests for AnalysisWorker — background MCPower runner."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication

from mcpower_gui.state import ModelState
from mcpower_gui.worker import AnalysisWorker

_app = QApplication.instance() or QApplication([])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def state():
    """Minimal valid ModelState for most tests."""
    s = ModelState()
    s.formula = "y = x1 + x2"
    s.effects = {"x1": 0.5, "x2": 0.3}
    return s


@pytest.fixture
def power_params():
    """Typical analysis_params for power mode."""
    return {
        "sample_size": 120,
        "correction": "",
        "scenarios": False,
        "target_test": "all",
        "test_formula": "",
    }


@pytest.fixture
def ss_params():
    """Typical analysis_params for sample_size mode."""
    return {
        "ss_from": 50,
        "ss_to": 300,
        "ss_by": 25,
        "correction": "Bonferroni",
        "scenarios": True,
        "target_test": "x1",
        "test_formula": "y ~ x1",
    }


@pytest.fixture
def mock_mcpower():
    """Mock MCPower class and its instance used inside worker.run()."""
    with patch("mcpower_gui.worker.MCPower") as MockMCPower:
        instance = MagicMock()
        instance.find_power.return_value = {"individual_powers": {"x1": 85.0}}
        instance.find_sample_size.return_value = {"first_achieved": {"x1": 100}}
        MockMCPower.return_value = instance
        yield MockMCPower, instance


# ---------------------------------------------------------------------------
# __init__ tests
# ---------------------------------------------------------------------------


class TestWorkerInit:
    """AnalysisWorker.__init__ snapshots state on the calling thread."""

    def test_snapshot_captured(self, state, power_params):
        worker = AnalysisWorker(state, "power", power_params)
        assert worker._snap["formula"] == "y = x1 + x2"
        assert worker._snap["effects"] == {"x1": 0.5, "x2": 0.3}

    def test_snapshot_is_independent_copy(self, state, power_params):
        worker = AnalysisWorker(state, "power", power_params)
        state.formula = "z = a + b"
        state.effects["x1"] = 999.0
        assert worker._snap["formula"] == "y = x1 + x2"
        assert worker._snap["effects"]["x1"] == 0.5

    def test_uploaded_data_none_by_default(self, state, power_params):
        worker = AnalysisWorker(state, "power", power_params)
        assert worker._uploaded_data is None

    def test_uploaded_data_deep_copied_as_lists(self, state, power_params):
        state.uploaded_data = {"x1": [1, 2, 3], "x2": [4, 5, 6]}
        worker = AnalysisWorker(state, "power", power_params)
        assert worker._uploaded_data == {"x1": [1, 2, 3], "x2": [4, 5, 6]}
        # Mutating original does not affect worker copy
        state.uploaded_data["x1"].append(99)
        assert worker._uploaded_data["x1"] == [1, 2, 3]

    def test_uploaded_data_values_converted_to_lists(self, state, power_params):
        """Even if source values are tuples or other iterables, they become lists."""
        state.uploaded_data = {"x1": (10, 20), "x2": (30, 40)}
        worker = AnalysisWorker(state, "power", power_params)
        assert isinstance(worker._uploaded_data["x1"], list)
        assert worker._uploaded_data["x1"] == [10, 20]

    def test_data_file_path_captured(self, state, power_params):
        state.data_file_path = "/path/to/data.csv"
        worker = AnalysisWorker(state, "power", power_params)
        assert worker._data_file_path == "/path/to/data.csv"

    def test_data_file_path_none_default(self, state, power_params):
        worker = AnalysisWorker(state, "power", power_params)
        assert worker._data_file_path is None

    def test_mode_stored(self, state, power_params):
        worker = AnalysisWorker(state, "power", power_params)
        assert worker._mode == "power"

    def test_mode_sample_size(self, state, ss_params):
        worker = AnalysisWorker(state, "sample_size", ss_params)
        assert worker._mode == "sample_size"

    def test_params_copied(self, state, power_params):
        worker = AnalysisWorker(state, "power", power_params)
        power_params["sample_size"] = 9999
        assert worker._params["sample_size"] == 120


# ---------------------------------------------------------------------------
# run() — full configuration sequence
# ---------------------------------------------------------------------------


class TestWorkerRunConfigSequence:
    """Verify the worker configures MCPower correctly before analysis."""

    def test_mcpower_created_with_formula(self, state, power_params, mock_mcpower):
        MockMCPower, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        MockMCPower.assert_called_once_with("y = x1 + x2")

    def test_set_effects_called(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        # Effects should include both x1 and x2
        args = instance.set_effects.call_args
        effects_str = args[0][0]
        assert "x1=0.5" in effects_str
        assert "x2=0.3" in effects_str

    def test_set_simulations_called_for_both_types(
        self, state, power_params, mock_mcpower
    ):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_simulations.assert_any_call(
            state.n_simulations, model_type="linear"
        )
        instance.set_simulations.assert_any_call(
            state.n_simulations_mixed_model, model_type="mixed"
        )

    def test_set_alpha_called(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_alpha.assert_called_once_with(0.05)

    def test_set_power_called(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_power.assert_called_once_with(80.0)

    def test_set_seed_called(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_seed.assert_called_once_with(2137)

    def test_set_max_failed_simulations_called(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_max_failed_simulations.assert_called_once_with(0.03)

    def test_set_parallel_called_when_not_false(
        self, state, power_params, mock_mcpower
    ):
        _, instance = mock_mcpower
        state.parallel = "mixedmodels"
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_parallel.assert_called_once_with(
            enable="mixedmodels", n_cores=state.n_cores
        )

    def test_set_parallel_skipped_when_false(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        state.parallel = False
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_parallel.assert_not_called()

    def test_apply_called(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance._apply.assert_called_once()

    def test_scenario_configs_set_when_present(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        # ModelState has non-empty scenario_configs by default
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_scenario_configs.assert_called_once()

    def test_scenario_configs_skipped_when_empty(
        self, state, power_params, mock_mcpower
    ):
        _, instance = mock_mcpower
        state.scenario_configs = {}
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_scenario_configs.assert_not_called()

    def test_correlations_set_when_present(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        state.correlations = {"x1,x2": 0.4}
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_correlations.assert_called_once_with("corr(x1, x2)=0.4")

    def test_correlations_skipped_when_empty(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        state.correlations = {}
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_correlations.assert_not_called()


# ---------------------------------------------------------------------------
# run() — uploaded data handling
# ---------------------------------------------------------------------------


class TestWorkerRunWithData:
    """Verify upload_data, variable type filtering, and data_types logic."""

    def test_upload_data_called_when_present(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        state.uploaded_data = {"x1": [1, 2, 3], "x2": [4, 5, 6]}
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.upload_data.assert_called_once()
        call_args = instance.upload_data.call_args
        assert call_args[0][0] == {"x1": [1, 2, 3], "x2": [4, 5, 6]}
        assert call_args[1]["preserve_correlation"] == "partial"
        assert call_args[1]["preserve_factor_level_names"] is True

    def test_upload_data_not_called_when_no_data(
        self, state, power_params, mock_mcpower
    ):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.upload_data.assert_not_called()

    def test_data_columns_excluded_from_variable_types(
        self, state, power_params, mock_mcpower
    ):
        """When data is uploaded, variable_types for data columns are NOT passed
        to set_variable_type — only non-data variables are."""
        _, instance = mock_mcpower
        state.uploaded_data = {"x1": [1, 2, 3], "x2": [4, 5, 6]}
        # x1 is in the data, x3 is NOT in the data
        state.variable_types = {
            "x1": {"type": "binary", "proportion": 0.5},
            "x3": {"type": "factor", "n_levels": 3},
        }
        state.formula = "y = x1 + x2 + x3"
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        # set_variable_type should only include x3
        vtype_call_args = instance.set_variable_type.call_args[0][0]
        assert "x3" in vtype_call_args
        assert "x1" not in vtype_call_args

    def test_set_variable_type_not_called_when_all_continuous(
        self, state, power_params, mock_mcpower
    ):
        _, instance = mock_mcpower
        state.variable_types = {"x1": {"type": "continuous"}}
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_variable_type.assert_not_called()

    def test_set_variable_type_called_for_non_continuous(
        self, state, power_params, mock_mcpower
    ):
        _, instance = mock_mcpower
        state.variable_types = {"x1": {"type": "binary", "proportion": 0.4}}
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_variable_type.assert_called_once()
        assert "x1=(binary, 0.4)" in instance.set_variable_type.call_args[0][0]

    def test_data_types_passed_when_reference_level_differs(
        self, state, power_params, mock_mcpower
    ):
        """build_data_types returns non-empty dict when reference level != first label."""
        _, instance = mock_mcpower
        state.uploaded_data = {"cyl": [4, 6, 8]}
        state.factor_level_labels = {"cyl": ["4", "6", "8"]}
        state.factor_reference_levels = {"cyl": "6"}  # differs from first ("4")
        state.formula = "y = cyl"
        state.effects = {"cyl[4]": 0.2, "cyl[8]": 0.3}
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        call_kwargs = instance.upload_data.call_args[1]
        assert call_kwargs["data_types"] == {"cyl": ("factor", "6")}

    def test_data_types_none_when_reference_level_is_default(
        self, state, power_params, mock_mcpower
    ):
        """data_types is None when reference level equals the first sorted label."""
        _, instance = mock_mcpower
        state.uploaded_data = {"cyl": [4, 6, 8]}
        state.factor_level_labels = {"cyl": ["4", "6", "8"]}
        state.factor_reference_levels = {"cyl": "4"}  # equals first label
        state.formula = "y = cyl"
        state.effects = {"cyl[6]": 0.2, "cyl[8]": 0.3}
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        call_kwargs = instance.upload_data.call_args[1]
        assert call_kwargs["data_types"] is None


# ---------------------------------------------------------------------------
# run() — cluster / mixed model configuration
# ---------------------------------------------------------------------------


class TestWorkerRunClusters:
    """Verify set_cluster is called correctly for mixed models."""

    def test_single_cluster(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        state.cluster_configs = [
            {"grouping_var": "school", "ICC": 0.2, "n_clusters": 20}
        ]
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_cluster.assert_called_once_with("school", ICC=0.2, n_clusters=20)

    def test_cluster_with_random_slopes(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        state.cluster_configs = [
            {
                "grouping_var": "school",
                "ICC": 0.15,
                "n_clusters": 30,
                "random_slopes": ["treatment"],
                "slope_variance": 0.1,
                "slope_intercept_corr": 0.3,
            }
        ]
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_cluster.assert_called_once_with(
            "school",
            ICC=0.15,
            n_clusters=30,
            random_slopes=["treatment"],
            slope_variance=0.1,
            slope_intercept_corr=0.3,
        )

    def test_cluster_with_n_per_parent(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        state.cluster_configs = [
            {"grouping_var": "classroom", "ICC": 0.1, "n_per_parent": 5}
        ]
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_cluster.assert_called_once_with(
            "classroom", ICC=0.1, n_per_parent=5
        )

    def test_multiple_clusters(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        state.cluster_configs = [
            {"grouping_var": "school", "ICC": 0.2, "n_clusters": 20},
            {"grouping_var": "district", "ICC": 0.05, "n_clusters": 5},
        ]
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        assert instance.set_cluster.call_count == 2
        instance.set_cluster.assert_any_call("school", ICC=0.2, n_clusters=20)
        instance.set_cluster.assert_any_call("district", ICC=0.05, n_clusters=5)

    def test_no_clusters_means_no_call(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        state.cluster_configs = []
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_cluster.assert_not_called()

    def test_cluster_without_random_slopes_omits_slope_kwargs(
        self, state, power_params, mock_mcpower
    ):
        """random_slopes falsy -> slope_variance and slope_intercept_corr not passed."""
        _, instance = mock_mcpower
        state.cluster_configs = [
            {
                "grouping_var": "school",
                "ICC": 0.2,
                "n_clusters": 20,
                "random_slopes": [],  # empty = falsy
            }
        ]
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        call_kwargs = instance.set_cluster.call_args[1]
        assert "random_slopes" not in call_kwargs
        assert "slope_variance" not in call_kwargs
        assert "slope_intercept_corr" not in call_kwargs


# ---------------------------------------------------------------------------
# run() — power mode
# ---------------------------------------------------------------------------


class TestWorkerRunPowerMode:
    """Verify find_power() is called with correct arguments."""

    def test_find_power_called(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.find_power.assert_called_once()

    def test_find_power_args(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        kwargs = instance.find_power.call_args[1]
        assert kwargs["sample_size"] == 120
        assert kwargs["target_test"] == "all"
        assert kwargs["correction"] is None  # empty string -> None
        assert kwargs["scenarios"] is False
        assert kwargs["summary"] == "short"
        assert kwargs["test_formula"] is None  # empty string -> None
        assert kwargs["print_results"] is False
        assert kwargs["return_results"] is True

    def test_find_power_with_correction(self, state, mock_mcpower):
        _, instance = mock_mcpower
        params = {
            "sample_size": 100,
            "correction": "Bonferroni",
            "scenarios": False,
            "target_test": "all",
            "test_formula": "",
        }
        worker = AnalysisWorker(state, "power", params)
        worker.run()
        kwargs = instance.find_power.call_args[1]
        assert kwargs["correction"] == "Bonferroni"

    def test_find_power_with_test_formula(self, state, mock_mcpower):
        _, instance = mock_mcpower
        params = {
            "sample_size": 100,
            "correction": "",
            "scenarios": False,
            "target_test": "x1",
            "test_formula": "y ~ x1",
        }
        worker = AnalysisWorker(state, "power", params)
        worker.run()
        kwargs = instance.find_power.call_args[1]
        assert kwargs["test_formula"] == "y ~ x1"
        assert kwargs["target_test"] == "x1"

    def test_find_power_default_sample_size(self, state, mock_mcpower):
        """When sample_size missing from params, default to 100."""
        _, instance = mock_mcpower
        params = {"correction": "", "scenarios": False, "target_test": "all"}
        worker = AnalysisWorker(state, "power", params)
        worker.run()
        kwargs = instance.find_power.call_args[1]
        assert kwargs["sample_size"] == 100

    def test_find_power_with_scenarios(self, state, mock_mcpower):
        _, instance = mock_mcpower
        params = {
            "sample_size": 100,
            "correction": "",
            "scenarios": True,
            "target_test": "all",
            "test_formula": "",
        }
        worker = AnalysisWorker(state, "power", params)
        worker.run()
        kwargs = instance.find_power.call_args[1]
        assert kwargs["scenarios"] is True

    def test_finished_signal_emitted(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        results = []
        worker.finished.connect(lambda d: results.append(d))
        worker.run()
        assert len(results) == 1

    def test_finished_signal_payload(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        results = []
        worker.finished.connect(lambda d: results.append(d))
        worker.run()
        payload = results[0]
        assert payload["mode"] == "power"
        assert payload["result"] == {"individual_powers": {"x1": 85.0}}
        assert payload["state_snapshot"]["formula"] == "y = x1 + x2"
        assert payload["analysis_params"]["sample_size"] == 120

    def test_finished_signal_includes_data_file_path(
        self, state, power_params, mock_mcpower
    ):
        _, instance = mock_mcpower
        state.data_file_path = "/tmp/my_data.csv"
        worker = AnalysisWorker(state, "power", power_params)
        results = []
        worker.finished.connect(lambda d: results.append(d))
        worker.run()
        assert results[0]["data_file_path"] == "/tmp/my_data.csv"

    def test_find_sample_size_not_called(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.find_sample_size.assert_not_called()


# ---------------------------------------------------------------------------
# run() — sample size mode
# ---------------------------------------------------------------------------


class TestWorkerRunSampleSizeMode:
    """Verify find_sample_size() is called with correct arguments."""

    def test_find_sample_size_called(self, state, ss_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "sample_size", ss_params)
        worker.run()
        instance.find_sample_size.assert_called_once()

    def test_find_sample_size_args(self, state, ss_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "sample_size", ss_params)
        worker.run()
        kwargs = instance.find_sample_size.call_args[1]
        assert kwargs["from_size"] == 50
        assert kwargs["to_size"] == 300
        assert kwargs["by"] == 25
        assert kwargs["target_test"] == "x1"
        assert kwargs["correction"] == "Bonferroni"
        assert kwargs["scenarios"] is True
        assert kwargs["summary"] == "short"
        assert kwargs["test_formula"] == "y ~ x1"
        assert kwargs["print_results"] is False
        assert kwargs["return_results"] is True

    def test_find_sample_size_defaults(self, state, mock_mcpower):
        """When ss_from/to/by are missing, defaults apply (30, 200, 10)."""
        _, instance = mock_mcpower
        params = {"correction": "", "scenarios": False, "target_test": "all"}
        worker = AnalysisWorker(state, "sample_size", params)
        worker.run()
        kwargs = instance.find_sample_size.call_args[1]
        assert kwargs["from_size"] == 30
        assert kwargs["to_size"] == 200
        assert kwargs["by"] == 10

    def test_finished_signal_emitted(self, state, ss_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "sample_size", ss_params)
        results = []
        worker.finished.connect(lambda d: results.append(d))
        worker.run()
        assert len(results) == 1
        assert results[0]["mode"] == "sample_size"
        assert results[0]["result"] == {"first_achieved": {"x1": 100}}

    def test_find_power_not_called(self, state, ss_params, mock_mcpower):
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "sample_size", ss_params)
        worker.run()
        instance.find_power.assert_not_called()


# ---------------------------------------------------------------------------
# run() — progress callback
# ---------------------------------------------------------------------------


class TestWorkerProgress:
    """Verify progress_callback and cancel_check are wired up."""

    def test_progress_callback_passed(self, state, power_params, mock_mcpower):
        """find_power receives a progress_callback that is callable."""
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        kwargs = instance.find_power.call_args[1]
        assert callable(kwargs["progress_callback"])

    def test_cancel_check_passed(self, state, power_params, mock_mcpower):
        """find_power receives a cancel_check that is callable."""
        _, instance = mock_mcpower
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        kwargs = instance.find_power.call_args[1]
        assert callable(kwargs["cancel_check"])

    def test_progress_signal_emitted_via_callback(
        self, state, power_params, mock_mcpower
    ):
        """When the progress_callback is invoked, the progress signal fires."""
        _, instance = mock_mcpower
        progress_reports = []

        def capture_find_power(**kwargs):
            cb = kwargs["progress_callback"]
            cb(5, 100)
            cb(50, 100)
            return {"individual_powers": {"x1": 85.0}}

        instance.find_power.side_effect = capture_find_power
        worker = AnalysisWorker(state, "power", power_params)
        worker.progress.connect(lambda cur, tot: progress_reports.append((cur, tot)))
        worker.run()
        assert (5, 100) in progress_reports
        assert (50, 100) in progress_reports


# ---------------------------------------------------------------------------
# run() — error handling
# ---------------------------------------------------------------------------


class TestWorkerErrorHandling:
    """Exception in run() -> error signal emitted with message."""

    def test_error_signal_on_exception(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        instance.find_power.side_effect = ValueError("something went wrong")
        worker = AnalysisWorker(state, "power", power_params)
        errors = []
        worker.error.connect(lambda s: errors.append(s))
        worker.run()
        assert len(errors) == 1
        assert "something went wrong" in errors[0]

    def test_finished_not_emitted_on_error(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        instance.find_power.side_effect = RuntimeError("boom")
        worker = AnalysisWorker(state, "power", power_params)
        results = []
        errors = []
        worker.finished.connect(lambda d: results.append(d))
        worker.error.connect(lambda s: errors.append(s))
        worker.run()
        assert len(results) == 0
        assert len(errors) == 1

    def test_error_from_apply(self, state, power_params, mock_mcpower):
        """Errors during model configuration also trigger error signal."""
        _, instance = mock_mcpower
        instance._apply.side_effect = TypeError("bad formula")
        worker = AnalysisWorker(state, "power", power_params)
        errors = []
        worker.error.connect(lambda s: errors.append(s))
        worker.run()
        assert len(errors) == 1
        assert "bad formula" in errors[0]

    def test_error_from_set_effects(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        instance.set_effects.side_effect = ValueError("invalid effect")
        worker = AnalysisWorker(state, "power", power_params)
        errors = []
        worker.error.connect(lambda s: errors.append(s))
        worker.run()
        assert len(errors) == 1
        assert "invalid effect" in errors[0]

    def test_error_signal_on_sample_size_exception(
        self, state, ss_params, mock_mcpower
    ):
        _, instance = mock_mcpower
        instance.find_sample_size.side_effect = RuntimeError("sample size fail")
        worker = AnalysisWorker(state, "sample_size", ss_params)
        errors = []
        worker.error.connect(lambda s: errors.append(s))
        worker.run()
        assert "sample size fail" in errors[0]


# ---------------------------------------------------------------------------
# run() — cancellation
# ---------------------------------------------------------------------------


class TestWorkerCancellation:
    """SimulationCancelled exception -> cancelled signal emitted."""

    def test_cancelled_signal_on_power(self, state, power_params, mock_mcpower):
        from mcpower.progress import SimulationCancelled

        _, instance = mock_mcpower
        instance.find_power.side_effect = SimulationCancelled()
        worker = AnalysisWorker(state, "power", power_params)
        cancels = []
        worker.cancelled.connect(lambda: cancels.append(True))
        worker.run()
        assert len(cancels) == 1

    def test_cancelled_signal_on_sample_size(self, state, ss_params, mock_mcpower):
        from mcpower.progress import SimulationCancelled

        _, instance = mock_mcpower
        instance.find_sample_size.side_effect = SimulationCancelled()
        worker = AnalysisWorker(state, "sample_size", ss_params)
        cancels = []
        worker.cancelled.connect(lambda: cancels.append(True))
        worker.run()
        assert len(cancels) == 1

    def test_finished_not_emitted_on_cancel(self, state, power_params, mock_mcpower):
        from mcpower.progress import SimulationCancelled

        _, instance = mock_mcpower
        instance.find_power.side_effect = SimulationCancelled()
        worker = AnalysisWorker(state, "power", power_params)
        results = []
        cancels = []
        worker.finished.connect(lambda d: results.append(d))
        worker.cancelled.connect(lambda: cancels.append(True))
        worker.run()
        assert len(results) == 0
        assert len(cancels) == 1

    def test_error_not_emitted_on_cancel(self, state, power_params, mock_mcpower):
        from mcpower.progress import SimulationCancelled

        _, instance = mock_mcpower
        instance.find_power.side_effect = SimulationCancelled()
        worker = AnalysisWorker(state, "power", power_params)
        errors = []
        cancels = []
        worker.error.connect(lambda s: errors.append(s))
        worker.cancelled.connect(lambda: cancels.append(True))
        worker.run()
        assert len(errors) == 0
        assert len(cancels) == 1


# ---------------------------------------------------------------------------
# run() — effects edge cases
# ---------------------------------------------------------------------------


class TestWorkerEffectsEdgeCases:
    """Edge cases around effects string construction."""

    def test_empty_effects_does_not_call_set_effects(
        self, state, power_params, mock_mcpower
    ):
        _, instance = mock_mcpower
        state.effects = {}
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_effects.assert_not_called()

    def test_single_effect(self, state, power_params, mock_mcpower):
        _, instance = mock_mcpower
        state.effects = {"x1": 0.7}
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        instance.set_effects.assert_called_once_with("x1=0.7")

    def test_factor_dummy_effects(self, state, power_params, mock_mcpower):
        """Factor dummies like cyl[6] should be in the effects string."""
        _, instance = mock_mcpower
        state.formula = "y = cyl"
        state.effects = {"cyl[6]": 0.2, "cyl[8]": 0.4}
        worker = AnalysisWorker(state, "power", power_params)
        worker.run()
        effects_str = instance.set_effects.call_args[0][0]
        assert "cyl[6]=0.2" in effects_str
        assert "cyl[8]=0.4" in effects_str
