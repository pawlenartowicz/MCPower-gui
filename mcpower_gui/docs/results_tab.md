# Results Tab

Each completed analysis creates a new closeable subtab in the Results tab. Subtabs are labeled with the mode (FP = Find Power, FSS = Find Sample Size) and the time of creation. Elapsed time is shown after one minute.

## Header

Each result panel starts with a header summarizing the analysis configuration: mode, model formula, test formula (if different), sample size or range, whether scenarios were enabled, and the correction method.

## Visualizations

### Find Power results

A **bar chart** shows the estimated power for each target test. A horizontal line marks the target power level. Bars reaching or exceeding the line indicate sufficient power.

### Find Sample Size results

A **power curve** plots power (y-axis) against sample size (x-axis) for each target test. Vertical markers indicate the first sample size where each test achieves the target power. A horizontal line marks the target power level.

## Results table

Below the chart, a table presents the numerical results:

- **Find Power:** Each row shows a predictor and its estimated power percentage. If correction is applied, both raw and corrected power are shown.
- **Find Sample Size:** Each row shows a predictor and the minimum sample size needed to reach the target power. If a test never reached the target within the search range, this is indicated.

## Scenario view

When scenarios are enabled, the visualization area becomes a tabbed view with three tabs (Optimistic, Realistic, Doomer), each containing its own chart. Below the scenario tabs, a combined summary table compares results across all three scenarios side by side.

## Replication script

At the bottom of each result panel, a read-only text box contains a Python script that reproduces the analysis using the MCPower library directly. This script captures all settings (formula, effects, variable types, correlations, analysis parameters) so you can run the same analysis outside the GUI.

## Export options

Three buttons appear below the script:

- **Copy Script** — Copies the replication script to the clipboard.
- **Save CSV** — Saves the results table (plus the replication script) as a CSV file.
- **Save Plots as JPG** — Exports all charts in the current result as JPG images (800px wide).
