"""Tests for factor autonaming — level_labels preserved through GUI widgets."""

import os
import sys
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from mcpower_gui.tabs.model_tab import ModelTab  # noqa: E402
from mcpower_gui.state import ModelState  # noqa: E402
from mcpower_gui.widgets.variable_type_editor import _PredictorRow  # noqa: E402
from mcpower_gui.widgets.anova_factor_editor import AnovaFactorEditor  # noqa: E402

CARS_CSV = str(Path(__file__).parent / "cars.csv")


class TestReadCarsCSV:
    def test_origin_is_string_column(self):
        data = ModelTab._read_csv(CARS_CSV)
        assert "origin" in data
        assert isinstance(data["origin"][0], str)

    def test_cyl_is_numeric(self):
        data = ModelTab._read_csv(CARS_CSV)
        assert "cyl" in data
        assert isinstance(data["cyl"][0], float)


class TestDetectTypesFromData:
    """Test that _detect_types_from_data produces level_labels for factors."""

    def test_origin_detected_as_factor_with_labels(self):
        state = ModelState()
        tab = ModelTab(state)
        data = ModelTab._read_csv(CARS_CSV)
        tab._detect_types_from_data(data)
        info = tab._data_detected["origin"]
        assert info["type"] == "factor"
        assert "level_labels" in info
        assert sorted(info["level_labels"]) == ["Europe", "Japan", "USA"]

    def test_cyl_detected_as_factor_with_labels(self):
        state = ModelState()
        tab = ModelTab(state)
        data = ModelTab._read_csv(CARS_CSV)
        tab._detect_types_from_data(data)
        info = tab._data_detected["cyl"]
        assert info["type"] == "factor"
        assert "level_labels" in info
        assert info["level_labels"] == ["4", "6", "8"]


class TestPredictorRowPreservesLevelLabels:
    """Test that _PredictorRow.get_info() returns level_labels when present."""

    def test_get_info_includes_level_labels(self):
        existing = {
            "type": "factor",
            "n_levels": 3,
            "proportions": [0.33, 0.33, 0.34],
            "level_labels": ["Europe", "Japan", "USA"],
        }
        row = _PredictorRow("origin", existing)
        info = row.get_info()
        assert info["type"] == "factor"
        assert info["level_labels"] == ["Europe", "Japan", "USA"]

    def test_get_info_no_level_labels_when_absent(self):
        existing = {
            "type": "factor",
            "n_levels": 3,
            "proportions": [0.33, 0.33, 0.34],
        }
        row = _PredictorRow("x1", existing)
        info = row.get_info()
        assert "level_labels" not in info

    def test_set_data_mode_stores_level_labels(self):
        existing = {"type": "factor", "n_levels": 3, "proportions": [0.33, 0.33, 0.34]}
        row = _PredictorRow("origin", existing)
        row.set_data_mode({"level_labels": ["Europe", "Japan", "USA"]})
        info = row.get_info()
        assert info["level_labels"] == ["Europe", "Japan", "USA"]


class TestAnovaEditorPreservesLevelLabels:
    """Test that AnovaFactorEditor.get_types() includes level_labels."""

    def test_get_types_includes_level_labels_from_data(self):
        editor = AnovaFactorEditor()
        factors = [
            {
                "name": "origin",
                "n_levels": 3,
                "proportions": [0.34, 0.22, 0.44],
                "level_labels": ["Europe", "Japan", "USA"],
            }
        ]
        editor.set_data_factors(factors)
        types = editor.get_types()
        assert "origin" in types
        assert types["origin"]["level_labels"] == ["Europe", "Japan", "USA"]

    def test_get_types_no_labels_without_data(self):
        editor = AnovaFactorEditor()
        # Manually add a factor (no data mode)
        editor._add_factor()
        types = editor.get_types()
        for name, info in types.items():
            assert "level_labels" not in info


class TestExpandPredictorsWithLabels:
    """Test that _expand_predictors uses level_labels for dummy names."""

    def test_string_factor_expansion(self):
        state = ModelState()
        tab = ModelTab(state)
        types = {
            "origin": {
                "type": "factor",
                "n_levels": 3,
                "level_labels": ["Europe", "Japan", "USA"],
            }
        }
        expanded, pred_types = tab._expand_predictors(["origin"], types)
        assert expanded == ["origin[Japan]", "origin[USA]"]
        assert pred_types["origin[Japan]"] == "factor"
        assert pred_types["origin[USA]"] == "factor"

    def test_numeric_factor_expansion(self):
        state = ModelState()
        tab = ModelTab(state)
        types = {
            "cyl": {
                "type": "factor",
                "n_levels": 3,
                "level_labels": ["4", "6", "8"],
            }
        }
        expanded, _ = tab._expand_predictors(["cyl"], types)
        assert expanded == ["cyl[6]", "cyl[8]"]

    def test_integer_fallback_without_labels(self):
        state = ModelState()
        tab = ModelTab(state)
        types = {"group": {"type": "factor", "n_levels": 3}}
        expanded, _ = tab._expand_predictors(["group"], types)
        assert expanded == ["group[2]", "group[3]"]

    def test_interaction_with_string_factor(self):
        state = ModelState()
        tab = ModelTab(state)
        types = {
            "origin": {
                "type": "factor",
                "n_levels": 3,
                "level_labels": ["Europe", "Japan", "USA"],
            },
            "hp": {"type": "continuous"},
        }
        expanded, _ = tab._expand_predictors(["origin:hp"], types)
        assert "origin[Japan]:hp" in expanded
        assert "origin[USA]:hp" in expanded


class TestRebuildEffectsFactorRefs:
    """Test that _rebuild_effects derives factor_refs in linear mode."""

    def test_linear_mode_derives_factor_refs(self):
        state = ModelState(
            formula="mpg = origin",
            predictors=["origin"],
            variable_types={
                "origin": {
                    "type": "factor",
                    "n_levels": 3,
                    "level_labels": ["Europe", "Japan", "USA"],
                }
            },
        )
        tab = ModelTab(state)
        tab._rebuild_effects()
        # Effects editor should have rows for Japan and USA (not Europe, it's ref)
        effect_names = list(tab.effects_editor.get_effects().keys())
        assert "origin[Japan]" in effect_names
        assert "origin[USA]" in effect_names
