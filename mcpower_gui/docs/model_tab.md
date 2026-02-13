# Model Tab

The Model tab is where you define your study design. It has five sections, worked through from top to bottom.

## Data Upload (optional)

Click **Upload CSV** to load an empirical dataset. When data is uploaded:

- Variable types are **auto-detected** from the data (2 unique values = binary, 3-6 = factor, 7+ = continuous).
- Correlations between variables are computed from the data.
- The type dropdowns are locked to the detected types.

You do not need to upload data — MCPower can generate synthetic data from your specifications alone.

### Correlation mode

When data is uploaded, the correlation mode controls how data-derived correlations interact with your manual settings:

- **strict** — Data-backed variable pairs are locked to their empirical correlations. Pairs without data can be edited manually. If no data variables match, correlations are disabled entirely.
- **partial** (default) — Data correlations are computed and shown, but you can override any pair. Your overrides are merged on top of the data correlations.
- **no** — Data correlations are ignored. Only your manually entered correlations are used.

## Model Formula

Enter an R-style formula describing your statistical model. Examples:

- `y = x1 + x2` — two predictors
- `y = x1 + x2 + x1:x2` — with interaction
- `y = x1 * x2` — shorthand (expands to main effects + interaction)
The formula is parsed live with a 400ms debounce. A green status line confirms successful parsing, showing the dependent variable and detected predictors. Red text indicates a parse error.

## Variable Types

Each predictor (excluding interactions) gets a row with a type selector:

- **continuous** — Standard normal variable. No extra parameters.
- **binary** — Two-level variable. Set the **proportion** of the higher level (default 0.5).
- **factor** — Categorical variable with 2-20 levels. Set the **number of levels** and the **proportion** of observations in each level. Use the "(to 100%)" button to normalize proportions to sum to 1.0.

Factor variables are automatically expanded into dummy-coded predictors (level 1 is the reference). For example, a 3-level factor `group` becomes `group[2]` and `group[3]` in the effects editor.

When data is uploaded, types are locked to the detected values and proportion controls are hidden.

## Effect Sizes

Each predictor (after factor expansion) gets a row with:

- A **spin box** for the standardized effect size (range -2.0 to 2.0).
- A **sign toggle** button to flip the sign.
- **S / M / L** buttons that set the value to a conventional effect size:

| Type | Small (S) | Medium (M) | Large (L) |
|---|---|---|---|
| Continuous | 0.10 | 0.25 | 0.40 |
| Binary | 0.20 | 0.50 | 0.80 |
| Factor | 0.20 | 0.50 | 0.80 |

The S/M/L buttons preserve the current sign (positive or negative). When the window is wide enough, the buttons expand to show full labels (small / medium / large).

## Correlations (optional)

If you have two or more continuous or binary predictors, a correlation triangle appears. Each pair gets a spin box for the Pearson correlation (range -1.0 to 1.0). Factor variables and interactions are excluded from the correlation matrix.

Correlations are used in the Cholesky decomposition during data generation to produce correlated predictor variables.
