# Find Power

Given a fixed sample size, estimate the statistical power for each predictor.

- **Sample size** — The total number of observations (20-100,000, default 100).
- Click **Run Power Analysis** to start.

Results show the estimated power (percentage of simulations where each effect was significant) for each target test.

## Test Formula

Use the **Test formula** field to evaluate power under model misspecification.
Enter a simpler formula than your model formula to see how omitting variables
affects power. The test formula must use a subset of variables from your model
formula. Leave empty to use the same formula for both data generation and testing.

## Running an analysis

Both buttons are disabled until a valid formula with at least one predictor is entered in the Model tab. While an analysis is running, a progress dialog shows the current simulation count. You can click **Abandon** in the progress dialog to cancel the analysis.
