# MCPower GUI

MCPower GUI is a desktop application for **Monte Carlo power analysis**. It provides a graphical interface to the [MCPower](https://github.com/freestylerscientist/MCPower) library, letting you plan sample sizes and estimate statistical power for complex study designs — without writing any code.

## What is power analysis?

Statistical power is the probability that a study will detect a real effect when one exists. A power analysis helps you determine:

- **Find Power:** Given a sample size, what is the probability of detecting your expected effects?
- **Find Sample Size:** What sample size do you need to achieve a target power level (e.g., 80%)?

## Why Monte Carlo simulation?

Traditional power formulas work for simple designs but break down with interactions, correlated predictors, categorical variables, or non-normal data. MCPower uses **Monte Carlo simulation** — it generates thousands of synthetic datasets under your assumptions, fits the statistical model to each, and counts how often the effects are detected. This approach handles arbitrary complexity.

## App workflow

1. **Model tab** — Define your study design: enter a formula, set variable types, specify effect sizes, and optionally upload empirical data with correlations.
2. **Analysis tab** — Choose analysis mode (Find Power or Find Sample Size), set target power, enable scenarios, and select multiple testing corrections.
3. **Results tab** — View power tables, bar charts, power curves, scenario comparisons, and a replication script you can run independently.

## Formula syntax

MCPower uses R-style formula notation:

| Formula | Meaning |
|---|---|
| `y = x1 + x2` | Two main effects |
| `y = x1 + x2 + x1:x2` | Two main effects + interaction |
| `y = x1 * x2` | Shorthand for `x1 + x2 + x1:x2` |
Both `=` and `~` are accepted as separators between the dependent variable and predictors.

**Note:** Mixed-effects models (e.g., `y ~ x + (1|school)`) are supported by the MCPower library but are not yet available in the GUI. Mixed model support in the app is planned for a future release.

## Installation

MCPower GUI is distributed as a standalone desktop application — no Python installation required.

- **Linux:** Download the `.bin` file, make it executable (`chmod +x mcpower-gui.bin`), and run it.
- **Windows:** Download the `.exe` file and run it.

Full documentation is available in-app via the **Documentation** menu item.

## Built on

MCPower GUI is built on [MCPower 0.4.0](https://github.com/freestylerscientist/MCPower).
