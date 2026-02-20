# ANOVA Factors

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
