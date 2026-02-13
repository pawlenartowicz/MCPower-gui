# Analysis Tab

The Analysis tab has three sections: common settings shared by both modes, and the two analysis modes.

## Common Analysis Settings

These settings apply to both Find Power and Find Sample Size:

- **Target power (%)** — The desired power level (1-99.99%, default 80%). Used as the threshold line in charts and as the goal for Find Sample Size.
- **Scenarios** — Check this to run the analysis under three assumption scenarios (Optimistic, Realistic, Doomer). See the Settings page for scenario parameter details.
- **Correction** — Multiple testing correction method: None, Bonferroni, Benjamini-Hochberg, or Holm. Applied to individual predictor p-values.
- **Target tests** — Select which predictors to include in the power analysis. "overall" tests the full model. Individual predictors can be selected or deselected.
- **Test formula** — An optional alternative formula for significance testing. Leave empty to use the model formula. Useful when you want to generate data with one model but test significance with a different (e.g., simpler) model.

## Find Power

Given a fixed sample size, estimate the statistical power for each predictor.

- **Sample size** — The total number of observations (20-100,000, default 100).
- Click **Run Power Analysis** to start.

Results show the estimated power (percentage of simulations where each effect was significant) for each target test.

## Find Sample Size

Search for the minimum sample size that achieves the target power.

- **From** — Starting sample size (default 30).
- **To** — Maximum sample size to try (default 200).
- **Step** — Increment between sample sizes (default 10).
- Click **Find Sample Size** to start.

The search evaluates power at each sample size in the range and reports the first sample size where each target test reaches the target power. Results include a power curve showing how power increases with sample size.

## Running an analysis

Both buttons are disabled until a valid formula with at least one predictor is entered in the Model tab. While an analysis is running, a progress dialog shows the current simulation count. You can click **Abandon** in the progress dialog to cancel the analysis.
