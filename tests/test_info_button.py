"""Tests for info_button module — per-page doc file validation."""

import pytest

from mcpower_gui._resources import resource_path

# All doc files referenced by _PAGES in documentation_dialog.py and by ? buttons
_DOC_FILES = {
    "overview.md": ["MCPower GUI", "power analysis"],
    "key_concepts.md": ["Statistical Power", "Monte Carlo"],
    "citation.md": ["cite", "BibTeX"],
    "input_mode.md": ["Linear Formula", "ANOVA"],
    "use_your_data.md": ["empirical dataset", "CSV file requirements"],
    "model_formula.md": ["R-style formula", "parsed live"],
    "variable_types.md": ["continuous", "binary", "factor"],
    "anova_factors.md": ["ANOVA mode", "Add Factor"],
    "effect_sizes.md": ["standardized effect size", "S / M / L"],
    "cluster_config.md": ["ICC", "N clusters"],
    "correlations.md": ["Cholesky", "correlation"],
    "data_preparation.md": ["CSV", "comma separators"],
    "mixed_models_guide.md": ["clustered", "Random intercepts"],
    "common_settings.md": ["Target power", "Correction"],
    "post_hoc.md": ["Pairwise Comparisons", "Select All"],
    "find_power.md": ["sample size", "Run Power Analysis"],
    "find_sample_size.md": ["minimum sample size", "Step"],
    "results.md": ["bar chart", "power curve", "Replication script"],
    "general_settings.md": ["Simulations", "Alpha", "Seed"],
    "scenario_settings.md": ["Heterogeneity", "Heteroskedasticity"],
}


class TestDocFiles:
    @pytest.mark.parametrize("filename", sorted(_DOC_FILES.keys()))
    def test_doc_file_exists(self, filename: str):
        path = resource_path("docs", filename)
        assert path.exists(), f"Doc file {filename} does not exist"

    @pytest.mark.parametrize("filename", sorted(_DOC_FILES.keys()))
    def test_doc_file_starts_with_h1(self, filename: str):
        path = resource_path("docs", filename)
        text = path.read_text(encoding="utf-8")
        assert text.startswith("# "), f"{filename} should start with # heading"

    @pytest.mark.parametrize(
        "filename,keywords",
        [(f, kw) for f, kw in sorted(_DOC_FILES.items())],
    )
    def test_doc_file_contains_keywords(self, filename: str, keywords: list[str]):
        path = resource_path("docs", filename)
        text = path.read_text(encoding="utf-8")
        for kw in keywords:
            assert kw in text, f"{filename} should contain '{kw}'"
