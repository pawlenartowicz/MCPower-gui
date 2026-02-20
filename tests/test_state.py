"""Tests for mcpower_gui.state — ModelState, variable type & correlation builders."""

import json

from mcpower_gui.state import (
    ModelState,
    build_correlations_string,
    build_variable_type_string,
)


class TestBuildVariableTypeString:
    def test_continuous_skipped(self):
        vtypes = {"x1": {"type": "continuous"}}
        assert build_variable_type_string(vtypes) == ""

    def test_binary(self):
        vtypes = {"x1": {"type": "binary", "proportion": 0.3}}
        assert build_variable_type_string(vtypes) == "x1=(binary, 0.3)"

    def test_factor_with_proportions(self):
        vtypes = {"x1": {"type": "factor", "proportions": [0.2, 0.3, 0.5]}}
        assert build_variable_type_string(vtypes) == "x1=(factor, 0.2, 0.3, 0.5)"

    def test_factor_with_n_levels(self):
        vtypes = {"x1": {"type": "factor", "n_levels": 4}}
        assert build_variable_type_string(vtypes) == "x1=(factor, 4)"

    def test_mixed(self):
        vtypes = {
            "x1": {"type": "continuous"},
            "x2": {"type": "binary", "proportion": 0.5},
            "x3": {"type": "factor", "n_levels": 3},
        }
        result = build_variable_type_string(vtypes)
        assert "x2=(binary, 0.5)" in result
        assert "x3=(factor, 3)" in result
        assert "x1" not in result

    def test_empty(self):
        assert build_variable_type_string({}) == ""


class TestBuildCorrelationsString:
    def test_single_pair(self):
        correlations = {"x1,x2": 0.3}
        assert build_correlations_string(correlations) == "corr(x1, x2)=0.3"

    def test_multiple_pairs(self):
        correlations = {"x1,x2": 0.3, "x2,x3": -0.5}
        result = build_correlations_string(correlations)
        assert "corr(x1, x2)=0.3" in result
        assert "corr(x2, x3)=-0.5" in result

    def test_empty(self):
        assert build_correlations_string({}) == ""


class TestModelState:
    def test_defaults(self):
        state = ModelState()
        assert state.formula == ""
        assert state.alpha == 0.05
        assert state.n_simulations == 1600
        assert state.target_power == 80.0
        assert state.seed == 2137
        assert state.parallel == "mixedmodels"

    def test_snapshot_returns_all_keys(self):
        state = ModelState()
        snap = state.snapshot()
        expected_keys = {
            "model_type",
            "formula",
            "dep_var",
            "predictors",
            "effects",
            "variable_types",
            "anova_factors",
            "anova_interactions",
            "n_simulations",
            "n_simulations_mixed_model",
            "alpha",
            "target_power",
            "seed",
            "max_failed_simulations",
            "parallel",
            "n_cores",
            "preserve_correlation",
            "correlations",
            "cluster_configs",
            "scenario_configs",
            "factor_level_labels",
            "factor_reference_levels",
            "uploaded_columns",
        }
        assert set(snap.keys()) == expected_keys

    def test_snapshot_is_json_serializable(self):
        state = ModelState(
            formula="y = x1 + x2",
            effects={"x1": 0.5, "x2": 0.3},
            variable_types={"x1": {"type": "binary", "proportion": 0.5}},
            correlations={"x1,x2": 0.2},
        )
        snap = state.snapshot()
        # Should not raise
        serialized = json.dumps(snap)
        roundtrip = json.loads(serialized)
        assert roundtrip["formula"] == "y = x1 + x2"
        assert roundtrip["effects"]["x1"] == 0.5

    def test_build_variable_type_string_method(self):
        state = ModelState(variable_types={"x1": {"type": "binary", "proportion": 0.4}})
        assert state.build_variable_type_string() == "x1=(binary, 0.4)"


class TestModelStateClusterConfigs:
    def test_default_cluster_configs_empty(self):
        state = ModelState()
        assert state.cluster_configs == []

    def test_snapshot_includes_cluster_configs(self):
        state = ModelState()
        state.cluster_configs = [
            {"grouping_var": "school", "ICC": 0.2, "n_clusters": 20}
        ]
        snap = state.snapshot()
        assert "cluster_configs" in snap
        assert snap["cluster_configs"] == [
            {"grouping_var": "school", "ICC": 0.2, "n_clusters": 20}
        ]

    def test_snapshot_cluster_configs_json_serializable(self):
        import json
        state = ModelState()
        state.cluster_configs = [
            {"grouping_var": "school", "ICC": 0.2, "n_clusters": 20,
             "random_slopes": ["x1"], "slope_variance": 0.1,
             "slope_intercept_corr": 0.3}
        ]
        snap = state.snapshot()
        serialized = json.dumps(snap)
        roundtrip = json.loads(serialized)
        assert roundtrip["cluster_configs"][0]["ICC"] == 0.2

    def test_snapshot_deep_copies_cluster_configs(self):
        state = ModelState()
        state.cluster_configs = [{"grouping_var": "school", "ICC": 0.2, "n_clusters": 20}]
        snap = state.snapshot()
        snap["cluster_configs"][0]["ICC"] = 0.9
        assert state.cluster_configs[0]["ICC"] == 0.2

    def test_snapshot_deep_copies_nested_lists(self):
        state = ModelState()
        state.cluster_configs = [
            {"grouping_var": "school", "ICC": 0.2, "random_slopes": ["x1"]}
        ]
        snap = state.snapshot()
        snap["cluster_configs"][0]["random_slopes"].append("x2")
        assert state.cluster_configs[0]["random_slopes"] == ["x1"]


def test_scenario_defaults_have_lme_keys():
    """SCENARIO_DEFAULTS must expose all LME perturbation keys for all 3 scenarios."""
    from mcpower_gui.state import SCENARIO_DEFAULTS

    lme_keys = {
        "icc_noise_sd", "random_effect_dist", "random_effect_df",
        "residual_dist", "residual_change_prob", "residual_df",
    }
    for scenario in ("optimistic", "realistic", "doomer"):
        missing = lme_keys - set(SCENARIO_DEFAULTS[scenario].keys())
        assert not missing, f"{scenario} is missing LME keys: {missing}"


def test_scenario_defaults_lme_values():
    """Optimistic LME keys are off; realistic/doomer match library defaults."""
    from mcpower_gui.state import SCENARIO_DEFAULTS

    opt = SCENARIO_DEFAULTS["optimistic"]
    assert opt["icc_noise_sd"] == 0.0
    assert opt["random_effect_dist"] == "normal"
    assert opt["residual_dist"] == "normal"
    assert opt["residual_change_prob"] == 0.0

    real = SCENARIO_DEFAULTS["realistic"]
    assert real["icc_noise_sd"] == 0.15
    assert real["random_effect_dist"] == "heavy_tailed"
    assert real["random_effect_df"] == 5
    assert real["residual_dist"] == "heavy_tailed"
    assert real["residual_change_prob"] == 0.3
    assert real["residual_df"] == 10

    doom = SCENARIO_DEFAULTS["doomer"]
    assert doom["icc_noise_sd"] == 0.30
    assert doom["random_effect_df"] == 3
    assert doom["residual_change_prob"] == 0.8
    assert doom["residual_df"] == 5


def test_scenario_configs_default_is_independent_copy():
    """Each ModelState instance gets its own scenario_configs copy."""
    from mcpower_gui.state import ModelState

    s1, s2 = ModelState(), ModelState()
    s1.scenario_configs["optimistic"]["icc_noise_sd"] = 99.0
    assert s2.scenario_configs["optimistic"]["icc_noise_sd"] == 0.0
