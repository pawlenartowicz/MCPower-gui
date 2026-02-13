# Settings

Open Settings from the menu bar. Changes are applied only when you click OK.

## General

- **Simulations (OLS)** — Number of Monte Carlo simulations for standard (OLS) models (100-100,000, default 1,600). More simulations = more precise power estimates but longer runtime.
- **Simulations (mixed)** — Number of simulations for mixed-effects models (100-100,000, default 400). Mixed models are slower, so a lower default is used.
- **Alpha** — Significance level (0.001-0.5, default 0.05). The probability threshold for rejecting the null hypothesis.
- **Seed** — Random number generator seed (default 2137). Set this for reproducible results. The same seed with the same settings produces the same power estimates.
- **Max failed sims** — Maximum proportion of simulations allowed to fail before raising an error (0.0-1.0, default 0.03). Relevant for mixed models where convergence failures can occur. Increase this for complex models.
- **Parallel** — Parallelization mode:
  - **Off** — All simulations run sequentially.
  - **On** — Parallel execution for all model types.
  - **Mixed models only** (default) — Parallel execution only for models with cluster specifications. OLS models stay sequential (they are already fast).
- **N cores** — Number of CPU cores for parallel execution:
  - **All - 1** — Uses all cores minus one (leaves one free for the system).
  - **Half** — Uses half the available cores.
  - **Custom** — Manually set the number of cores.

## Scenario Parameters

Scenarios test your power analysis under progressively more pessimistic assumptions about real-world data. Each scenario has four parameters:

### Heterogeneity (0-2, default: Optimistic=0, Realistic=0.2, Doomer=0.4)

Adds random variation to the effect sizes across simulations. A value of 0.2 means each simulation's true effect is drawn from a distribution centered on your specified effect with SD = 0.2. This models the reality that true effects may vary across replications.

### Heteroskedasticity (-1 to 1, default: Optimistic=0, Realistic=0.1, Doomer=0.2)

Introduces unequal error variance that depends on predictor values. Positive values mean higher predictor values produce more variance in the outcome. This violates the homoskedasticity assumption of OLS regression.

### Correlation noise SD (0-2, default: Optimistic=0, Realistic=0.2, Doomer=0.4)

Adds random noise to the correlation structure between predictors. Higher values mean the actual correlations in each simulated dataset deviate more from your specified values. This models uncertainty in the true correlation structure.

### Distribution change prob (0-1, default: Optimistic=0, Realistic=0.3, Doomer=0.6)

The probability that each predictor's distribution is changed from normal to a non-normal form (skewed, high kurtosis, or uniform) in a given simulation. This tests robustness to violations of the normality assumption.
