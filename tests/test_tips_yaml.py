"""Validate tips.yaml structure and completeness."""

from pathlib import Path

import yaml

from mcpower_gui.widgets.tip_engine import TipEngine

TIPS_PATH = Path(__file__).resolve().parent.parent / "mcpower_gui" / "tips.yaml"

VALID_STYLES = {"done", "next", "optional", "normal"}
VALID_TYPES = {"text", "formula_examples"}
VALID_TABS = {"model", "analysis"}
REQUIRED_KEYS = {"id", "tab", "style", "priority", "conditions"}

VALID_STATE_KEYS = {
    "tab", "mode", "formula", "has_effects", "has_non_continuous",
    "has_clusters", "clusters_configured", "clusters_resolved",
    "data_uploaded", "data_filename", "data_rows", "corr_mode",
    "correlable_count", "data_section_open", "corr_section_open",
    "model_ready", "has_factors", "n_predictors", "formula_display",
}


def _load_tips():
    with open(TIPS_PATH) as f:
        return yaml.safe_load(f)


class TestTipsYamlStructure:
    def test_file_exists(self):
        assert TIPS_PATH.exists(), f"tips.yaml not found at {TIPS_PATH}"

    def test_is_list(self):
        tips = _load_tips()
        assert isinstance(tips, list), "tips.yaml root must be a list"

    def test_required_keys_present(self):
        for tip in _load_tips():
            for key in REQUIRED_KEYS:
                assert key in tip, f"Tip {tip.get('id', '???')} missing key: {key}"

    def test_ids_unique(self):
        ids = [t["id"] for t in _load_tips()]
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {[x for x in ids if ids.count(x) > 1]}"

    def test_valid_styles(self):
        for tip in _load_tips():
            if tip.get("type") == "formula_examples":
                continue
            assert tip["style"] in VALID_STYLES, (
                f"Tip {tip['id']}: invalid style '{tip['style']}'"
            )

    def test_valid_tabs(self):
        for tip in _load_tips():
            assert tip["tab"] in VALID_TABS, (
                f"Tip {tip['id']}: invalid tab '{tip['tab']}'"
            )

    def test_valid_types(self):
        for tip in _load_tips():
            tip_type = tip.get("type", "text")
            assert tip_type in VALID_TYPES, (
                f"Tip {tip['id']}: invalid type '{tip_type}'"
            )

    def test_conditions_use_known_keys(self):
        for tip in _load_tips():
            for key in tip["conditions"]:
                assert key in VALID_STATE_KEYS, (
                    f"Tip {tip['id']}: unknown condition key '{key}'"
                )

    def test_all_tips_have_text_or_type(self):
        for tip in _load_tips():
            has_text = bool(tip.get("text", "").strip())
            has_type = tip.get("type", "text") != "text"
            assert has_text or has_type, (
                f"Tip {tip['id']}: must have text or a non-text type"
            )


class TestTipsYamlCoverage:
    """Verify key user states have at least one matching tip."""

    def _evaluate(self, state):
        tips = _load_tips()
        engine = TipEngine(tips)
        return engine.evaluate(state)

    def test_linear_no_formula(self):
        result = self._evaluate({
            "tab": "model", "mode": "linear", "formula": "",
            "has_effects": False, "data_section_open": False,
            "corr_section_open": False,
        })
        assert len(result) >= 1, "No tip for linear mode with empty formula"

    def test_anova_no_factors(self):
        result = self._evaluate({
            "tab": "model", "mode": "anova", "formula": "",
            "has_effects": False, "data_section_open": False,
            "corr_section_open": False,
        })
        assert len(result) >= 1, "No tip for ANOVA with no factors"

    def test_formula_no_effects(self):
        result = self._evaluate({
            "tab": "model", "mode": "linear", "formula": "y = x1 + x2",
            "has_effects": False, "has_clusters": False,
            "clusters_resolved": True,
            "data_section_open": False, "corr_section_open": False,
            "formula_display": "y = x1 + x2",
        })
        assert any(t.style == "next" for t in result), "No 'next' tip for formula without effects"

    def test_model_ready(self):
        result = self._evaluate({
            "tab": "model", "mode": "linear", "formula": "y = x1",
            "has_effects": True, "has_clusters": False,
            "clusters_configured": False, "clusters_resolved": True,
            "data_section_open": False, "corr_section_open": False,
            "formula_display": "y = x1",
        })
        assert any(t.style == "done" for t in result), "No 'done' tip for ready model"

    def test_data_section_no_upload(self):
        result = self._evaluate({
            "tab": "model", "mode": "linear",
            "data_section_open": True, "data_uploaded": False,
        })
        assert any(t.style == "next" for t in result), "No tip when data section open, no upload"

    def test_data_section_uploaded(self):
        result = self._evaluate({
            "tab": "model", "mode": "linear",
            "data_section_open": True, "data_uploaded": True,
            "data_filename": "test.csv", "data_rows": 100,
        })
        assert any(t.style == "done" for t in result), "No done tip when data uploaded"

    def test_corr_section_no_data(self):
        result = self._evaluate({
            "tab": "model", "mode": "linear",
            "corr_section_open": True, "data_uploaded": False,
            "correlable_count": 3, "data_section_open": False,
        })
        assert len(result) >= 1, "No tip for corr section without data"

    def test_mixed_model_clusters_needed(self):
        result = self._evaluate({
            "tab": "model", "mode": "linear", "formula": "y ~ x + (1|g)",
            "has_effects": False, "has_clusters": True,
            "clusters_configured": False,
            "data_section_open": False, "corr_section_open": False,
            "formula_display": "y ~ x + (1|g)",
        })
        assert any("cluster" in t.text.lower() for t in result), "No cluster tip for mixed model"

    def test_analysis_not_ready(self):
        result = self._evaluate({
            "tab": "analysis", "model_ready": False,
        })
        assert len(result) >= 1, "No tip for analysis tab when model not ready"

    def test_analysis_ready(self):
        result = self._evaluate({
            "tab": "analysis", "model_ready": True,
            "formula_display": "y = x1", "n_predictors": 1,
            "has_factors": False,
        })
        assert any(t.style == "done" for t in result), "No done tip for analysis with ready model"

    def test_progress_supplement_data_section(self):
        result = self._evaluate({
            "tab": "model", "mode": "linear",
            "formula": "y = x1", "has_effects": False,
            "has_clusters": False, "clusters_resolved": True,
            "data_section_open": True, "data_uploaded": False,
            "corr_section_open": False,
            "formula_display": "y = x1",
        })
        assert any("effect" in t.text.lower() for t in result), (
            "No model progress tip when data section open and effects missing"
        )
