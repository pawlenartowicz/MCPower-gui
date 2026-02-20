"""Tests for FormulaInput random effects parsing."""

import pytest
from PySide6.QtWidgets import QApplication

from mcpower_gui.widgets.formula_input import FormulaInput

# Ensure a QApplication exists for the entire test module.
_app = QApplication.instance() or QApplication([])


@pytest.fixture
def formula_input():
    widget = FormulaInput()
    yield widget
    widget.deleteLater()


class TestFormulaInputRandomEffects:
    def test_no_random_effects(self, formula_input):
        """Formula without random effects emits empty list."""
        results = []
        formula_input.formula_changed.connect(
            lambda f, d, p, r: results.append(r)
        )
        formula_input.set_formula("y = x1 + x2")
        assert len(results) == 1
        assert results[0] == []

    def test_random_intercept(self, formula_input):
        """Formula with (1|school) emits random_intercept."""
        results = []
        formula_input.formula_changed.connect(
            lambda f, d, p, r: results.append(r)
        )
        formula_input.set_formula("y ~ x1 + (1|school)")
        assert len(results) == 1
        re = results[0]
        assert len(re) == 1
        assert re[0]["type"] == "random_intercept"
        assert re[0]["grouping_var"] == "school"

    def test_random_slope(self, formula_input):
        """Formula with (1+x|school) emits random_slope."""
        results = []
        formula_input.formula_changed.connect(
            lambda f, d, p, r: results.append(r)
        )
        formula_input.set_formula("y ~ x1 + (1 + x1|school)")
        assert len(results) == 1
        re = results[0]
        assert len(re) == 1
        assert re[0]["type"] == "random_slope"
        assert re[0]["grouping_var"] == "school"
        assert "x1" in re[0]["slope_vars"]

    def test_nested_effects(self, formula_input):
        """Formula with (1|school/classroom) emits nested random effects."""
        results = []
        formula_input.formula_changed.connect(
            lambda f, d, p, r: results.append(r)
        )
        formula_input.set_formula("y ~ x1 + (1|school/classroom)")
        assert len(results) == 1
        re = results[0]
        assert len(re) == 2  # parser expands nested to 2 terms

    def test_status_shows_random_effects(self, formula_input):
        """Status label includes random effects info."""
        formula_input.set_formula("y ~ x1 + (1|school)")
        assert "Random" in formula_input._status.text()

    def test_predictors_exclude_random_effects(self, formula_input):
        """Predictors list should NOT include grouping variables."""
        results = []
        formula_input.formula_changed.connect(
            lambda f, d, p, r: results.append(p)
        )
        formula_input.set_formula("y ~ x1 + x2 + (1|school)")
        preds = results[0]
        assert "x1" in preds
        assert "x2" in preds
        assert "school" not in preds
