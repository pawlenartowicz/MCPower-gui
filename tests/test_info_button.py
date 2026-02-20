"""Tests for info_button module — section extraction logic."""

from mcpower_gui.widgets.info_button import extract_doc_section


class TestExtractDocSection:
    def test_extracts_known_section(self):
        text = extract_doc_section("model_tab.md", "Model Formula")
        assert text.startswith("## Model Formula")
        assert "R-style formula" in text

    def test_extracts_section_with_subsections(self):
        text = extract_doc_section("model_tab.md", "Use Your Data (optional)")
        assert "## Use Your Data (optional)" in text
        assert "### Correlation mode" in text

    def test_extracts_last_section(self):
        text = extract_doc_section("model_tab.md", "Correlations (optional)")
        assert text.startswith("## Correlations (optional)")
        assert "Cholesky" in text

    def test_section_not_found(self):
        text = extract_doc_section("model_tab.md", "Nonexistent Section")
        assert "not found" in text

    def test_settings_general(self):
        text = extract_doc_section("settings.md", "General")
        assert "Simulations" in text

    def test_settings_scenario_parameters(self):
        text = extract_doc_section("settings.md", "Scenario Parameters")
        assert "Heterogeneity" in text
        assert "Heteroskedasticity" in text

    def test_analysis_find_power(self):
        text = extract_doc_section("analysis_tab.md", "Find Power")
        assert "sample size" in text.lower()
        assert "Run Power Analysis" in text
