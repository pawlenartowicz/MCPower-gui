# Model Tab

The Model tab is where you define your study design. It has five sections, worked through from top to bottom.

## Input Mode

Choose between two modes for defining your model:

- **Linear Formula** — Enter an R-style formula (e.g. `y = x1 + x2 + x1:x2`). You control variable types (continuous, binary, factor) and correlations manually. Suitable for regression models with mixed predictor types.
- **ANOVA** — Define factors and their levels directly. All predictors are treated as categorical factors. Correlations are not applicable in ANOVA mode.

The input mode toggle switches the visible sections below: Linear Formula mode shows the Model Formula and Variable Types sections, while ANOVA mode shows the ANOVA Factors section.

## Use Your Data (optional)

By default, MCPower **generates synthetic data** from your specifications (formula, variable types, effect sizes). This works well for most power analyses.

If you have an **empirical dataset**, you can upload it here. MCPower will then use your real data's structure instead of generating synthetic data. When data is uploaded:

- Variable types are **auto-detected** from the data (2 unique values = binary, 3-6 = factor, 7+ = continuous).
- **String columns** are supported — columns with non-numeric values (e.g. "control", "drug_a", "drug_b") are auto-detected as factors if they have 2-20 unique values.
- Factor levels use the **original values from the data** (e.g. `cyl` with values 4, 6, 8 produces dummies `cyl[6]`, `cyl[8]` with `cyl[4]` as reference).
- The first sorted value is the default **reference level** (alphabetically for strings, numerically for numbers). In ANOVA mode, you can change the reference level with a dropdown selector.
- Correlations between variables are computed from the data.
- The type dropdowns are locked to the detected types.

### CSV file requirements

The GUI reads CSV files using Python's built-in `csv` module. Your file should:

- **Use comma separators** (not semicolons or tabs).
- **Include a header row** with column names.
- **Have consistent data types per column** — don't mix numbers and text in the same column.
- **Avoid special characters in column names** — stick to letters, numbers, and underscores.
- **Have no missing values or empty cells** — fill or remove incomplete rows before uploading.
- **Use UTF-8 encoding** (most editors default to this).

Numeric columns are auto-converted to numbers. Non-numeric columns (e.g. "control", "drug_a") are kept as strings and treated as factors. Columns named "" or starting with "Unnamed" (common index columns from spreadsheet exports) are automatically skipped.

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

Mixed-model formulas are also supported — use `(1|group)` for random intercepts and `(1 + x|group)` for random slopes. For example: `y ~ x1 + x2 + (1|school)` or `y ~ x1 + (1 + x1|school)`. When random effects are detected, the Cluster Configuration section appears automatically below.

## Cluster Configuration

This section appears automatically when your formula includes random effects (e.g., `(1|school)`). Each random effect term gets a configuration card with the following parameters:

- **ICC (Intraclass Correlation Coefficient)** — The proportion of total variance due to differences between clusters (range 0.00–0.99, default 0.20). Higher ICC means more clustering.
- **N clusters** — The number of groups (range 2–10,000, default 20). More clusters generally improve power more than larger clusters.

For random slope models (e.g., `(1 + x1|school)`), two additional parameters appear:

- **Slope variance** — The variance of the random slope across clusters (range 0.00–10.00, default 0.10).
- **Slope-intercept corr** — The correlation between random intercepts and random slopes (range -1.00 to 1.00, default 0.00).

For nested random effects (e.g., `(1|school/class)`), child terms show **N per parent** instead of N clusters — the number of sub-groups within each parent group.

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
