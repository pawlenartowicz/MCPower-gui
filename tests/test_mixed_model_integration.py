"""Integration tests for mixed model GUI pipeline."""

import json

from mcpower_gui.script_generator import generate_script
from mcpower_gui.state import ModelState


class TestMixedModelStateRoundTrip:
    """Test state snapshot/restore with cluster configs."""

    def test_snapshot_roundtrip_intercept(self):
        state = ModelState(
            formula="y ~ x1 + (1|school)",
            predictors=["x1"],
            effects={"x1": 0.5},
            cluster_configs=[
                {"grouping_var": "school", "ICC": 0.2, "n_clusters": 20}
            ],
        )
        snap = state.snapshot()
        serialized = json.dumps(snap)
        restored = json.loads(serialized)
        assert restored["cluster_configs"] == [
            {"grouping_var": "school", "ICC": 0.2, "n_clusters": 20}
        ]

    def test_snapshot_roundtrip_slope(self):
        state = ModelState(
            formula="y ~ x1 + (1 + x1|school)",
            cluster_configs=[
                {
                    "grouping_var": "school",
                    "ICC": 0.2,
                    "n_clusters": 20,
                    "random_slopes": ["x1"],
                    "slope_variance": 0.1,
                    "slope_intercept_corr": 0.3,
                }
            ],
        )
        snap = state.snapshot()
        serialized = json.dumps(snap)
        restored = json.loads(serialized)
        cfg = restored["cluster_configs"][0]
        assert cfg["random_slopes"] == ["x1"]
        assert cfg["slope_variance"] == 0.1

    def test_snapshot_roundtrip_nested(self):
        state = ModelState(
            formula="y ~ x1 + (1|school/classroom)",
            cluster_configs=[
                {"grouping_var": "school", "ICC": 0.15, "n_clusters": 10},
                {"grouping_var": "school:classroom", "ICC": 0.10, "n_per_parent": 3},
            ],
        )
        snap = state.snapshot()
        assert len(snap["cluster_configs"]) == 2


class TestMixedModelScriptGeneration:
    """Test that generated scripts include correct set_cluster calls."""

    def test_script_with_intercept_is_valid_python(self):
        state = ModelState(
            formula="y ~ x1 + (1|school)",
            effects={"x1": 0.5},
            cluster_configs=[
                {"grouping_var": "school", "ICC": 0.2, "n_clusters": 20}
            ],
        )
        snap = state.snapshot()
        params = {"sample_size": 600, "target_test": "all"}
        script = generate_script(snap, params, mode="power")
        compile(script, "<test>", "exec")
        assert "set_cluster" in script

    def test_script_with_slope_is_valid_python(self):
        state = ModelState(
            formula="y ~ x1 + (1 + x1|school)",
            effects={"x1": 0.5},
            cluster_configs=[
                {
                    "grouping_var": "school",
                    "ICC": 0.2,
                    "n_clusters": 20,
                    "random_slopes": ["x1"],
                    "slope_variance": 0.1,
                    "slope_intercept_corr": 0.3,
                }
            ],
        )
        snap = state.snapshot()
        params = {"sample_size": 1000, "target_test": "all"}
        script = generate_script(snap, params, mode="power")
        compile(script, "<test>", "exec")
        assert "random_slopes" in script

    def test_script_with_nested_is_valid_python(self):
        state = ModelState(
            formula="y ~ x1 + (1|school/classroom)",
            effects={"x1": 0.5},
            cluster_configs=[
                {"grouping_var": "school", "ICC": 0.15, "n_clusters": 10},
                {"grouping_var": "school:classroom", "ICC": 0.10, "n_per_parent": 3},
            ],
        )
        snap = state.snapshot()
        params = {"sample_size": 1500, "target_test": "all"}
        script = generate_script(snap, params, mode="power")
        compile(script, "<test>", "exec")
        assert script.count("set_cluster") == 2

    def test_script_without_clusters_has_no_set_cluster(self):
        state = ModelState(
            formula="y = x1 + x2",
            effects={"x1": 0.5, "x2": 0.3},
        )
        snap = state.snapshot()
        params = {"sample_size": 100, "target_test": "all"}
        script = generate_script(snap, params, mode="power")
        assert "set_cluster" not in script
