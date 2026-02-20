# Mixed Models Guide

This guide explains when and how to use mixed-effects models (also called multilevel or hierarchical models) in MCPower GUI.

## When to use mixed models

Use a mixed-effects model when your data has a **clustered or hierarchical structure** — observations grouped within higher-level units. Common examples:

- Students nested within **schools**
- Patients nested within **hospitals**
- Measurements nested within **participants** (repeated measures)
- Employees nested within **companies**

Ignoring clustering leads to **inflated Type I error rates** (false positives) because observations within the same cluster are not independent.

## Formula syntax

Add random effects to your formula using the `(1|group)` syntax:

- `y ~ x1 + x2 + (1|school)` — Random intercepts for schools
- `y ~ x1 + (1 + x1|school)` — Random intercepts and random slopes for x1
- `y ~ x1 + (1|school/class)` — Nested random effects (classes within schools)

When random effects are detected, the **Cluster Configuration** section appears automatically in the Model tab.

## Key parameters

### ICC (Intraclass Correlation Coefficient)

The proportion of total variance due to differences between clusters. Range: 0.00–0.99, default: 0.20.

- **Low ICC (< 0.10):** Minimal clustering, mixed model may not be necessary.
- **Moderate ICC (0.10–0.30):** Typical in educational and clinical research.
- **High ICC (> 0.30):** Strong clustering, substantial impact on power.

### Number of clusters

How many groups in your study. Range: 2–10,000, default: 20.

- More clusters generally improve power **more** than larger clusters.
- Aim for **20–30 clusters minimum** (50+ is ideal).
- Ensure at least **5 observations per cluster** (10+ recommended).

### Random slopes

For `(1 + x|group)` models, two additional parameters:

- **Slope variance** — How much the predictor's effect varies across clusters (default: 0.10).
- **Slope-intercept correlation** — Whether clusters with higher intercepts also have steeper slopes (default: 0.00).

## Design effect

Clustering reduces the effective sample size:

```
Design Effect = 1 + (cluster_size - 1) × ICC
Effective N = Total N / Design Effect
```

For example, with 600 observations in 30 clusters (20 per cluster) and ICC = 0.2:
- Design Effect = 1 + 19 × 0.2 = 4.8
- Effective N = 600 / 4.8 = 125

## Convergence

Mixed models are more computationally intensive and may occasionally fail to converge. If you see convergence warnings:

- Increase the **Max failed sims** setting (Settings → General) to allow more failures.
- Ensure you have enough observations per cluster (at least 5, preferably 10+).
- Simplify the random effects structure if possible.

For more detail, see the [Mixed-Effects Models](https://github.com/pawlenartowicz/MCPower/wiki/Concept-Mixed-Effects) concept guide.
