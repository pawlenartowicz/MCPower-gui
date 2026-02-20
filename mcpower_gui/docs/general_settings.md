# General Settings

Open Settings from the menu bar. Changes are applied only when you click OK.

- **Simulations (OLS)** — Number of Monte Carlo simulations for standard (OLS) models (100-100,000, default 1,600). More simulations = more precise power estimates but longer runtime.
- **Simulations (mixed)** — Number of simulations for mixed-effects models (100-100,000, default 800). Mixed models are slower, so a lower default is used.
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
