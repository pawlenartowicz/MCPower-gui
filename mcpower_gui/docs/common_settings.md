# Common Analysis Settings

These settings apply to both Find Power and Find Sample Size:

- **Target power (%)** — The desired power level (1-99.99%, default 80%). Used as the threshold line in charts and as the goal for Find Sample Size.
- **Scenarios** — Check this to run the analysis under three assumption scenarios (Optimistic, Realistic, Doomer). See the Settings page for scenario parameter details.
- **Correction** — Multiple testing correction method: None, Bonferroni, Benjamini-Hochberg, Holm, or Tukey HSD. Applied to individual predictor p-values. Tukey HSD is specifically designed for post hoc pairwise comparisons — when selected, non-contrast tests show "-" for corrected power.
- **Target tests** — Select which predictors to include in the power analysis. "overall" tests the full model. Individual predictors can be selected or deselected.
- **Test formula** — An optional alternative formula for significance testing. Leave empty to use the model formula. Useful when you want to generate data with one model but test significance with a different (e.g., simpler) model.
