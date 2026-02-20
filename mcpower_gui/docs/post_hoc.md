# Post Hoc Pairwise Comparisons

When your model includes factor variables (categorical predictors), a "Post Hoc Pairwise Comparisons" section appears below the common settings. This section lists all possible pairwise comparisons between factor levels.

When data is uploaded, comparisons use the **original level names** from the data. For example, a factor `origin` with values ["Europe", "Japan", "USA"] generates:
- origin[Europe] vs origin[Japan]
- origin[Europe] vs origin[USA]
- origin[Japan] vs origin[USA]

Without uploaded data, comparisons use integer indices (e.g. `group[1] vs group[2]`).

All comparisons are **unchecked by default** — you must explicitly select which pairwise comparisons to include. Selected comparisons are appended to the target tests and appear in the results alongside the main effects.

Use the "Select All" checkbox to quickly select or deselect all comparisons. For Tukey HSD correction on post hoc comparisons, select "Tukey HSD" from the Correction dropdown.
