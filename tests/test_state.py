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
            "formula",
            "dep_var",
            "predictors",
            "effects",
            "variable_types",
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
            "scenario_configs",
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
        state = ModelState(
            variable_types={"x1": {"type": "binary", "proportion": 0.4}}
        )
        assert state.build_variable_type_string() == "x1=(binary, 0.4)"
