# Model Tab

The Model tab is where you define your study design. It has five sections, worked through from top to bottom.

## Input Mode

Choose between two modes for defining your model:

- **Linear Formula** — Enter an R-style formula (e.g. `y = x1 + x2 + x1:x2`). You control variable types (continuous, binary, factor) and correlations manually. Suitable for regression models with mixed predictor types.
- **ANOVA** — Define factors and their levels directly. All predictors are treated as categorical factors. Correlations are not applicable in ANOVA mode.

The input mode toggle switches the visible sections below: Linear Formula mode shows the Model Formula and Variable Types sections, while ANOVA mode shows the ANOVA Factors section.

## Data Upload (optional)

Click **Upload CSV** to load an empirical dataset. When data is uploaded:

- Variable types are **auto-detected** from the data (2 unique values = binary, 3-6 = factor, 7+ = continuous).
- **String columns** are supported — columns with non-numeric values (e.g. "control", "drug_a", "drug_b") are auto-detected as factors if they have 2-20 unique values.
- Factor levels use the **original values from the data** (e.g. `cyl` with values 4, 6, 8 produces dummies `cyl[6]`, `cyl[8]` with `cyl[4]` as reference).
- The first sorted value is the default **reference level** (alphabetically for strings, numerically for numbers). In ANOVA mode, you can change the reference level with a dropdown selector.
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

Factor variables are automatically expanded into dummy-coded predictors. When data is uploaded, dummies use the **original level names** from the data — for example, a factor `cyl` with values [4, 6, 8] becomes `cyl[6]` and `cyl[8]` (with `cyl[4]` as reference). String factors like `origin` with values ["Europe", "Japan", "USA"] become `origin[Japan]` and `origin[USA]` (with "Europe" as reference). Without uploaded data, integer indices are used: a 3-level factor `group` becomes `group[2]` and `group[3]` (level 1 is reference).

When data is uploaded, types are locked to the detected values and proportion controls are hidden.

## ANOVA Factors

In ANOVA mode, factors are defined directly instead of using a formula. Each factor row has:

- **Name** — The factor name (e.g. "treatment", "group").
- **Levels** — Number of levels (2-20).
- **Proportions** — The proportion of observations in each level. Use the "(to 100%)" button to normalize.
- **X** button — Remove the factor.

Click **+ Add Factor** to add additional factors. When two or more factors are defined, an **Include interactions** checkbox appears, letting you select which factor pairs have interaction terms.

When data is uploaded in ANOVA mode:
- Factor names, level counts, and proportions are auto-detected from the data and locked.
- **Original level labels** are displayed (e.g. "Levels: Europe, Japan, USA").
- A **Reference** dropdown lets you choose which level serves as the reference category. The default is the first sorted value.

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
