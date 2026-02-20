# Variable Types

Each predictor (excluding interactions) gets a row with a type selector:

- **continuous** — Standard normal variable. No extra parameters.
- **binary** — Two-level variable. Set the **proportion** of the higher level (default 0.5).
- **factor** — Categorical variable with 2-20 levels. Set the **number of levels** and the **proportion** of observations in each level. Use the "(to 100%)" button to normalize proportions to sum to 1.0.

Factor variables are automatically expanded into dummy-coded predictors. When data is uploaded, dummies use the **original level names** from the data — for example, a factor `cyl` with values [4, 6, 8] becomes `cyl[6]` and `cyl[8]` (with `cyl[4]` as reference). String factors like `origin` with values ["Europe", "Japan", "USA"] become `origin[Japan]` and `origin[USA]` (with "Europe" as reference). Without uploaded data, integer indices are used: a 3-level factor `group` becomes `group[2]` and `group[3]` (level 1 is reference).

When data is uploaded, types are locked to the detected values and proportion controls are hidden.

For more detail, see the [Variable Types](https://github.com/pawlenartowicz/MCPower/wiki/Concept-Variable-Types) concept guide.
