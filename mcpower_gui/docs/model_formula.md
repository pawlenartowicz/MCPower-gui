# Model Formula

Enter an R-style formula describing your statistical model. Examples:

- `y = x1 + x2` — two predictors
- `y = x1 + x2 + x1:x2` — with interaction
- `y = x1 * x2` — shorthand (expands to main effects + interaction)

The formula is parsed live with a 400ms debounce. A green status line confirms successful parsing, showing the dependent variable and detected predictors. Red text indicates a parse error.

Mixed-model formulas are also supported — use `(1|group)` for random intercepts and `(1 + x|group)` for random slopes. For example: `y ~ x1 + x2 + (1|school)` or `y ~ x1 + (1 + x1|school)`. When random effects are detected, the Cluster Configuration section appears automatically below.
