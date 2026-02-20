"""Tests for TipEngine — declarative tip rule evaluation."""

from mcpower_gui.widgets.tip_engine import ResolvedTip, TipEngine


def _rule(**overrides):
    """Helper: create a rule dict with sensible defaults."""
    base = {
        "id": "test",
        "tab": "model",
        "text": "tip text",
        "style": "normal",
        "priority": 100,
        "conditions": {},
    }
    base.update(overrides)
    return base


class TestExactStringMatch:
    """1. Exact string match (match and no-match)."""

    def test_matches_when_equal(self):
        engine = TipEngine([_rule(conditions={"formula": "y ~ x"})])
        result = engine.evaluate({"tab": "model", "formula": "y ~ x"})
        assert len(result) == 1
        assert result[0].id == "test"

    def test_fails_when_not_equal(self):
        engine = TipEngine([_rule(conditions={"formula": "y ~ x"})])
        result = engine.evaluate({"tab": "model", "formula": "y ~ z"})
        assert len(result) == 0


class TestBooleanMatch:
    """2. Boolean match (match and no-match)."""

    def test_matches_when_true(self):
        engine = TipEngine([_rule(conditions={"has_data": True})])
        result = engine.evaluate({"tab": "model", "has_data": True})
        assert len(result) == 1

    def test_fails_when_false(self):
        engine = TipEngine([_rule(conditions={"has_data": True})])
        result = engine.evaluate({"tab": "model", "has_data": False})
        assert len(result) == 0


class TestNotEmptyOperator:
    """3. !empty operator (non-empty passes, empty fails)."""

    def test_non_empty_passes(self):
        engine = TipEngine([_rule(conditions={"formula": "!empty"})])
        result = engine.evaluate({"tab": "model", "formula": "y ~ x"})
        assert len(result) == 1

    def test_empty_fails(self):
        engine = TipEngine([_rule(conditions={"formula": "!empty"})])
        result = engine.evaluate({"tab": "model", "formula": ""})
        assert len(result) == 0

    def test_missing_key_fails(self):
        engine = TipEngine([_rule(conditions={"formula": "!empty"})])
        result = engine.evaluate({"tab": "model"})
        assert len(result) == 0


class TestNotValueOperator:
    """4. !value operator (not-equal passes, equal fails)."""

    def test_not_equal_passes(self):
        engine = TipEngine([_rule(conditions={"status": "!done"})])
        result = engine.evaluate({"tab": "model", "status": "pending"})
        assert len(result) == 1

    def test_equal_fails(self):
        engine = TipEngine([_rule(conditions={"status": "!done"})])
        result = engine.evaluate({"tab": "model", "status": "done"})
        assert len(result) == 0


class TestGreaterOrEqualOperator:
    """5. >=N operator (above/at/below threshold)."""

    def test_above_threshold_passes(self):
        engine = TipEngine([_rule(conditions={"n_effects": ">=3"})])
        result = engine.evaluate({"tab": "model", "n_effects": 5})
        assert len(result) == 1

    def test_at_threshold_passes(self):
        engine = TipEngine([_rule(conditions={"n_effects": ">=3"})])
        result = engine.evaluate({"tab": "model", "n_effects": 3})
        assert len(result) == 1

    def test_below_threshold_fails(self):
        engine = TipEngine([_rule(conditions={"n_effects": ">=3"})])
        result = engine.evaluate({"tab": "model", "n_effects": 2})
        assert len(result) == 0


class TestEmptyStringMatch:
    """6. Empty string match ("" matches only empty)."""

    def test_empty_matches_empty(self):
        engine = TipEngine([_rule(conditions={"formula": ""})])
        result = engine.evaluate({"tab": "model", "formula": ""})
        assert len(result) == 1

    def test_empty_does_not_match_non_empty(self):
        engine = TipEngine([_rule(conditions={"formula": ""})])
        result = engine.evaluate({"tab": "model", "formula": "y ~ x"})
        assert len(result) == 0


class TestAndLogic:
    """7. All conditions must match (AND logic)."""

    def test_all_match(self):
        engine = TipEngine([_rule(conditions={"formula": "!empty", "has_data": True})])
        result = engine.evaluate({"tab": "model", "formula": "y ~ x", "has_data": True})
        assert len(result) == 1

    def test_one_fails(self):
        engine = TipEngine([_rule(conditions={"formula": "!empty", "has_data": True})])
        result = engine.evaluate(
            {"tab": "model", "formula": "y ~ x", "has_data": False}
        )
        assert len(result) == 0


class TestNoConditions:
    """8. No conditions = always matches."""

    def test_always_matches(self):
        engine = TipEngine([_rule(conditions={})])
        result = engine.evaluate({"tab": "model"})
        assert len(result) == 1

    def test_always_matches_no_conditions_key(self):
        rule = _rule()
        del rule["conditions"]
        engine = TipEngine([rule])
        result = engine.evaluate({"tab": "model"})
        assert len(result) == 1


class TestTabFiltering:
    """9. Tab filtering (only matching tab returned)."""

    def test_matching_tab(self):
        engine = TipEngine(
            [
                _rule(id="model_tip", tab="model"),
                _rule(id="analysis_tip", tab="analysis"),
            ]
        )
        result = engine.evaluate({"tab": "model"})
        assert len(result) == 1
        assert result[0].id == "model_tip"

    def test_non_matching_tab(self):
        engine = TipEngine([_rule(id="analysis_tip", tab="analysis")])
        result = engine.evaluate({"tab": "model"})
        assert len(result) == 0


class TestPrioritySorting:
    """10. Priority sorting (lower first)."""

    def test_sorted_by_priority(self):
        engine = TipEngine(
            [
                _rule(id="low", priority=300),
                _rule(id="high", priority=100),
                _rule(id="mid", priority=200),
            ]
        )
        result = engine.evaluate({"tab": "model"})
        assert [t.id for t in result] == ["high", "mid", "low"]


class TestTextInterpolation:
    """11. Text interpolation (with present and missing variables)."""

    def test_present_variable(self):
        engine = TipEngine([_rule(text="Hello {user}!")])
        result = engine.evaluate({"tab": "model", "user": "Alice"})
        assert result[0].text == "Hello Alice!"

    def test_missing_variable_preserved(self):
        engine = TipEngine([_rule(text="Hello {user}! You have {count} items.")])
        result = engine.evaluate({"tab": "model", "user": "Alice"})
        assert result[0].text == "Hello Alice! You have {count} items."


class TestDefaultType:
    """12. Default type is "text", custom type preserved."""

    def test_default_type(self):
        engine = TipEngine([_rule()])
        result = engine.evaluate({"tab": "model"})
        assert result[0].tip_type == "text"

    def test_custom_type(self):
        engine = TipEngine([_rule(type="formula_examples")])
        result = engine.evaluate({"tab": "model"})
        assert result[0].tip_type == "formula_examples"


class TestMissingStateKey:
    """13. Missing state key makes condition fail."""

    def test_missing_key_fails_exact(self):
        engine = TipEngine([_rule(conditions={"formula": "y ~ x"})])
        result = engine.evaluate({"tab": "model"})
        assert len(result) == 0

    def test_missing_key_fails_gte(self):
        engine = TipEngine([_rule(conditions={"n_effects": ">=3"})])
        result = engine.evaluate({"tab": "model"})
        assert len(result) == 0

    def test_missing_key_fails_not_value(self):
        engine = TipEngine([_rule(conditions={"status": "!done"})])
        result = engine.evaluate({"tab": "model"})
        assert len(result) == 0


class TestResolvedTipDataclass:
    """Verify ResolvedTip is frozen and has expected fields."""

    def test_frozen(self):
        tip = ResolvedTip(id="t", text="hi", style="normal", tip_type="text")
        try:
            tip.id = "other"  # type: ignore[misc]
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass

    def test_fields(self):
        tip = ResolvedTip(id="t", text="hi", style="done", tip_type="formula_examples")
        assert tip.id == "t"
        assert tip.text == "hi"
        assert tip.style == "done"
        assert tip.tip_type == "formula_examples"


class TestYamlIntegration:
    """Test TipEngine loaded with the real tips.yaml file."""

    @staticmethod
    def _load_engine():
        from pathlib import Path

        import yaml

        tips_path = (
            Path(__file__).resolve().parent.parent
            / "mcpower_gui"
            / "tips.yaml"
        )
        with open(tips_path) as f:
            rules = yaml.safe_load(f)
        return TipEngine(rules)

    def test_linear_empty_formula_shows_formula_examples_widget(self):
        engine = self._load_engine()
        result = engine.evaluate(
            {
                "tab": "model",
                "mode": "linear",
                "formula": "",
                "has_effects": False,
                "data_section_open": False,
                "corr_section_open": False,
            }
        )
        types = [t.tip_type for t in result]
        assert "formula_examples" in types

    def test_anova_empty_formula_no_formula_examples(self):
        engine = self._load_engine()
        result = engine.evaluate(
            {
                "tab": "model",
                "mode": "anova",
                "formula": "",
                "has_effects": False,
                "data_section_open": False,
                "corr_section_open": False,
            }
        )
        types = [t.tip_type for t in result]
        assert "formula_examples" not in types
