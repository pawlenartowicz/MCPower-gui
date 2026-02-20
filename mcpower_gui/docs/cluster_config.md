# Cluster Configuration

This section appears automatically when your formula includes random effects (e.g., `(1|school)`). Each random effect term gets a configuration card with the following parameters:

- **ICC (Intraclass Correlation Coefficient)** — The proportion of total variance due to differences between clusters (range 0.00–0.99, default 0.20). Higher ICC means more clustering.
- **N clusters** — The number of groups (range 2–10,000, default 20). More clusters generally improve power more than larger clusters.

For random slope models (e.g., `(1 + x1|school)`), two additional parameters appear:

- **Slope variance** — The variance of the random slope across clusters (range 0.00–10.00, default 0.10).
- **Slope-intercept corr** — The correlation between random intercepts and random slopes (range -1.00 to 1.00, default 0.00).

For nested random effects (e.g., `(1|school/class)`), child terms show **N per parent** instead of N clusters — the number of sub-groups within each parent group.

For more detail, see the [Mixed-Effects Models](https://github.com/pawlenartowicz/MCPower/wiki/Concept-Mixed-Effects) concept guide.
