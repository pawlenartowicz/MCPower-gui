"""Background worker for running MCPower analyses off the UI thread."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from mcpower import MCPower

from mcpower_gui.state import (
    ModelState,
    build_correlations_string,
    build_variable_type_string,
)


class AnalysisWorker(QThread):
    """Runs MCPower analysis in a background thread.

    All state is snapshot in __init__ (called on the UI thread).
    The MCPower instance is created and used only inside run() (worker thread).
    """

    finished = Signal(dict)  # emits result dict on success
    error = Signal(str)  # emits error message on failure
    progress = Signal(int, int)  # emits (current, total) for progress tracking
    cancelled = Signal()  # emits when simulation is cancelled by user

    def __init__(
        self,
        state: ModelState,
        mode: str,
        analysis_params: dict,
        parent=None,
    ):
        """
        Parameters
        ----------
        state : ModelState
            Snapshot of all current model settings.
        mode : str
            "power" for find_power, "sample_size" for find_sample_size.
        analysis_params : dict
            Per-run parameters from the Analysis tab (sample_size, correction,
            scenarios, summary, target_test, test_formula, ss_from/to/by).
        """
        super().__init__(parent)
        # Snapshot model state on the UI thread
        self._snap = state.snapshot()
        self._uploaded_data = (
            {k: list(v) for k, v in state.uploaded_data.items()}
            if state.uploaded_data is not None
            else None
        )
        self._data_file_path = state.data_file_path
        self._mode = mode
        self._params = dict(analysis_params)

    def run(self):
        try:
            from mcpower.progress import SimulationCancelled

            def _on_progress(current, total):
                self.progress.emit(current, total)

            def cancel_check():
                return self.isInterruptionRequested()

            snap = self._snap
            model = MCPower(snap["formula"])

            # Upload data if present (before set_variable_type and set_effects)
            if self._uploaded_data is not None:
                # Build data_types with reference levels for non-default refs
                data_types = {}
                factor_refs = snap.get("factor_reference_levels", {})
                factor_labels = snap.get("factor_level_labels", {})
                for factor_name, ref_level in factor_refs.items():
                    level_labels = factor_labels.get(factor_name, [])
                    if level_labels and ref_level != level_labels[0]:
                        # Non-default reference — pass as tuple
                        data_types[factor_name] = ("factor", ref_level)

                model.upload_data(
                    self._uploaded_data,
                    preserve_correlation=snap["preserve_correlation"],
                    preserve_factor_level_names=True,
                    data_types=data_types if data_types else None,
                )

            # Set variable types if any non-continuous.
            # When data is uploaded, exclude data columns — _apply_data handles
            # their type detection (with correct level labels).  Calling
            # set_variable_type for those columns would create integer-indexed
            # dummies that shadow the data-detected labels.
            if self._uploaded_data is not None:
                data_cols = set(self._uploaded_data.keys())
                filtered_vtypes = {
                    k: v
                    for k, v in snap["variable_types"].items()
                    if k not in data_cols
                }
            else:
                filtered_vtypes = snap["variable_types"]
            vtype_str = build_variable_type_string(filtered_vtypes)
            if vtype_str:
                model.set_variable_type(vtype_str)

            # Build effects string: "x1=0.5, x2[2]=0.3"
            effects_str = ", ".join(
                f"{name}={value}" for name, value in snap["effects"].items()
            )
            if effects_str:
                model.set_effects(effects_str)

            # Configure clusters for mixed models
            for cluster_cfg in snap.get("cluster_configs", []):
                kwargs: dict = {"ICC": cluster_cfg["ICC"]}
                if "n_clusters" in cluster_cfg:
                    kwargs["n_clusters"] = cluster_cfg["n_clusters"]
                if "n_per_parent" in cluster_cfg:
                    kwargs["n_per_parent"] = cluster_cfg["n_per_parent"]
                if cluster_cfg.get("random_slopes"):
                    kwargs["random_slopes"] = cluster_cfg["random_slopes"]
                    kwargs["slope_variance"] = cluster_cfg.get("slope_variance", 0.0)
                    kwargs["slope_intercept_corr"] = cluster_cfg.get(
                        "slope_intercept_corr", 0.0
                    )
                model.set_cluster(cluster_cfg["grouping_var"], **kwargs)

            model.set_simulations(snap["n_simulations"], model_type="linear")
            model.set_simulations(snap["n_simulations_mixed_model"], model_type="mixed")
            model.set_alpha(snap["alpha"])
            model.set_power(snap["target_power"])
            model.set_seed(snap["seed"])
            model.set_max_failed_simulations(snap["max_failed_simulations"])
            if snap["parallel"] is not False:
                model.set_parallel(enable=snap["parallel"], n_cores=snap["n_cores"])
            if snap["scenario_configs"]:
                model.set_scenario_configs(snap["scenario_configs"])
            if snap["correlations"]:
                model.set_correlations(build_correlations_string(snap["correlations"]))
            model.apply()

            # Extract per-run params
            correction = self._params.get("correction") or None
            scenarios = self._params.get("scenarios", False)
            summary = "short"
            target_test = self._params.get("target_test", "all")
            test_formula = self._params.get("test_formula", "")

            if self._mode == "power":
                result = model.find_power(
                    sample_size=self._params.get("sample_size", 100),
                    target_test=target_test,
                    correction=correction,
                    scenarios=scenarios,
                    summary=summary,
                    test_formula=test_formula or None,
                    print_results=False,
                    return_results=True,
                    progress_callback=_on_progress,
                    cancel_check=cancel_check,
                )
            else:
                result = model.find_sample_size(
                    from_size=self._params.get("ss_from", 30),
                    to_size=self._params.get("ss_to", 200),
                    by=self._params.get("ss_by", 10),
                    target_test=target_test,
                    correction=correction,
                    scenarios=scenarios,
                    summary=summary,
                    test_formula=test_formula or None,
                    print_results=False,
                    return_results=True,
                    progress_callback=_on_progress,
                    cancel_check=cancel_check,
                )

            self.finished.emit(
                {
                    "mode": self._mode,
                    "result": result,
                    "data_file_path": self._data_file_path,
                    "state_snapshot": snap,
                    "analysis_params": self._params,
                }
            )

        except SimulationCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.error.emit(str(exc))
