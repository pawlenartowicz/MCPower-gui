# Key Concepts

## Statistical Power

Statistical power is the probability of correctly rejecting the null hypothesis when the alternative is true — in other words, the chance your study will detect a real effect. Convention targets 80% power, meaning a 20% chance of a false negative (Type II error).

Power depends on four factors:
- **Effect size** — Larger effects are easier to detect.
- **Sample size** — More data gives more power.
- **Alpha level** — A more lenient threshold (e.g., 0.10 vs 0.05) increases power but also increases false positives.
- **Variability** — More noise in the data reduces power.

## Monte Carlo Simulation

Instead of using closed-form formulas (which only exist for simple designs), MCPower estimates power by simulation:

1. Generate a synthetic dataset under your specified model (effects, variable types, correlations, sample size).
2. Fit the statistical model (OLS regression) to the synthetic data.
3. Check whether each effect is statistically significant (p < alpha).
4. Repeat steps 1-3 many times (e.g., 1,600 simulations).
5. Power = the proportion of simulations where the effect was significant.

This approach handles any model complexity: interactions, correlated predictors, categorical variables, non-normal distributions, and clustered data.

## Effect Sizes

Effect sizes in MCPower are **standardized regression coefficients (betas)**. They represent the expected change in the outcome (in standard deviations) per one standard deviation change in the predictor.

Conventional benchmarks (Cohen's guidelines):

| Type | Small | Medium | Large |
|---|---|---|---|
| Continuous | 0.10 | 0.25 | 0.40 |
| Binary/Factor | 0.20 | 0.50 | 0.80 |

Negative effect sizes indicate inverse relationships. The sign affects the direction but not the power (power depends on the magnitude).

For more detail, see the [Effect Sizes](https://github.com/pawlenartowicz/MCPower/wiki/Concept-Effect-Sizes) concept guide.

## Variable Types and Distributions

### Continuous
Standard normal distribution (mean=0, SD=1). When empirical data is uploaded, the actual distribution is preserved.

### Binary
Two-level variable (0/1). The **proportion** parameter sets the probability of the higher level. Default is 0.50 (balanced groups).

### Factor
Categorical variable with 2-20 levels. Internally represented as dummy variables. A 3-level factor produces two dummy predictors. Each level has a proportion parameter controlling how observations are distributed across categories.

When data is uploaded, factor dummies use the **original values** from the data as level names. For example, `cyl` with values [4, 6, 8] produces dummies `cyl[6]` and `cyl[8]`, with `cyl[4]` as the reference. **String columns** are also supported — `origin` with values ["Europe", "Japan", "USA"] produces `origin[Japan]` and `origin[USA]`, with "Europe" as the reference. The default reference level is the first sorted value (alphabetically for strings, numerically for numbers).

Without uploaded data, levels are integer-indexed: a 3-level factor `group` produces dummies `group[2]` and `group[3]`, with level 1 as reference.

For more detail, see the [Variable Types](https://github.com/pawlenartowicz/MCPower/wiki/Concept-Variable-Types) concept guide.

## Interactions

Interaction terms (e.g., `x1:x2`) test whether the effect of one predictor depends on the level of another. In the formula, use `:` for a specific interaction or `*` as shorthand for all main effects plus their interaction.

When a factor variable is involved in an interaction, it is expanded into all combinations of the factor's dummy levels. For example, `x1:group` with a 3-level factor `group` becomes `x1:group[2]` and `x1:group[3]` (or `x1:group[B]` and `x1:group[C]` when data with named levels is uploaded).

## Post Hoc Comparisons

Post hoc (pairwise) comparisons test for differences between specific pairs of factor levels after finding a significant overall effect. For example, if a 3-level factor "treatment" is significant overall, post hoc comparisons tell you which specific pairs differ.

When data is uploaded, pairwise comparisons use the **original level names**: e.g. `origin[Europe] vs origin[Japan]`, `origin[Europe] vs origin[USA]`, `origin[Japan] vs origin[USA]`. Without uploaded data, comparisons use integer indices: `treatment[1] vs treatment[2]`, `treatment[1] vs treatment[3]`, `treatment[2] vs treatment[3]`.

Post hoc comparisons use individual t-tests by default. To control the family-wise error rate across multiple comparisons, apply a correction method:
- **Tukey HSD** — Designed specifically for pairwise comparisons. Controls family-wise error rate while maintaining good power. When applied, only contrast-based tests (pairwise comparisons) receive corrected p-values; non-contrast tests show "-".
- **Bonferroni / Holm / Benjamini-Hochberg** — General-purpose corrections that also work with post hoc comparisons.

## Multiple Testing Corrections

When testing multiple predictors, the chance of at least one false positive increases. Corrections adjust p-values to control for this:

- **Bonferroni** — Multiplies each p-value by the number of tests. Most conservative.
- **Holm** — A step-down version of Bonferroni. Less conservative, still controls the family-wise error rate.
- **Benjamini-Hochberg** — Controls the false discovery rate (FDR). Least conservative, more power.
- **Tukey HSD** — Specifically designed for pairwise comparisons between factor levels. Only applies to contrast-based tests (post hoc comparisons); non-contrast tests show "-" for corrected power.

Corrections reduce power for individual tests. If you only care about the overall model test, you may not need a correction.

For more detail, see the [Correlations](https://github.com/pawlenartowicz/MCPower/wiki/Concept-Correlations) concept guide.

## Scenario Analysis

Scenarios test how robust your power estimates are to violations of statistical assumptions. Three progressively pessimistic scenarios are available:

- **Optimistic** — Your exact specifications (no violations). This is the baseline.
- **Realistic** — Moderate violations: some heterogeneity in effects, mild heteroskedasticity, correlation noise, and occasional non-normal distributions.
- **Doomer** — Severe violations: substantial effect heterogeneity, notable heteroskedasticity, large correlation noise, and frequent non-normality.

Scenario parameters are configured in Settings. Running with scenarios enabled gives you a range of power estimates rather than a single point estimate.

For more detail, see the [Scenario Analysis](https://github.com/pawlenartowicz/MCPower/wiki/Concept-Scenario-Analysis) concept guide.

## Mixed-Effects Models

Mixed-effects models handle **clustered data** — observations grouped within higher-level units (e.g., students within schools, patients within hospitals). When you enter a formula with random effects, the cluster configuration editor appears automatically in the Model tab.

MCPower supports three random effect structures:

- **Random intercepts** `(1|group)` — Per-cluster intercept. The simplest and most common structure.
- **Random slopes** `(1 + x|group)` — Per-cluster intercept and slope. Allows the effect of a predictor to vary across clusters.
- **Nested effects** `(1|group/subgroup)` — Hierarchical random intercepts at multiple levels (e.g., students in classrooms in schools).

### Key parameters

- **ICC (Intraclass Correlation Coefficient)** — The proportion of total variance due to differences between clusters. Higher ICC means more clustering, which reduces effective sample size.
- **Number of clusters** — How many groups. More clusters generally improve power more than larger clusters.

For random slopes, two additional parameters:

- **Slope variance** — How much the predictor's effect varies across clusters.
- **Slope-intercept correlation** — Whether clusters with higher intercepts also have steeper slopes.

For nested effects, child terms use **N per parent** — the number of sub-groups within each parent group.

### Design effect

Clustering reduces the effective sample size:

```
Design Effect = 1 + (cluster_size - 1) * ICC
Effective N = Total N / Design Effect
```

For example, with 600 observations in 30 clusters (20 per cluster) and ICC = 0.2:
- Design Effect = 1 + 19 * 0.2 = 4.8
- Effective N = 600 / 4.8 = 125

You need roughly 4.8 times more observations than a non-clustered design for the same power.

### Design recommendations

- Aim for 20-30 clusters minimum (50+ is ideal).
- Ensure at least 5 observations per cluster (10+ recommended).
- Lower ICC is better for power (ICC < 0.2 is manageable, ICC > 0.4 is challenging).
- Increasing the number of clusters is generally more effective than increasing cluster size.
- Random slopes and nested models may have higher convergence failure rates — increase the "Max failed sims" setting if needed.

For more detail, see the [Mixed-Effects Models](https://github.com/pawlenartowicz/MCPower/wiki/Concept-Mixed-Effects) concept guide.
