# Changelog

All notable changes to MCPower GUI are documented in this file.

## [Unreleased]

### Added

- **ANOVA mode** — New input mode toggle (Linear Formula / ANOVA) in the Model tab. ANOVA mode provides a dedicated factor editor with named levels, proportions, reference level selector, and interaction toggles. Tukey HSD correction is available exclusively in ANOVA mode
- **Contextual help (info buttons)** — Small (i) buttons next to every QGroupBox title across Model, Analysis, and Settings. Clicking opens a popup with the relevant documentation section; a link at the bottom opens the full documentation dialog on the correct page (`info_button.py`)
- **Named factor levels** — When data is uploaded, factor dummies use original values from the data (e.g. `cyl[6]`, `cyl[8]` instead of `cyl[2]`, `cyl[3]`)
- **String column support** — Columns with non-numeric values (e.g. "control", "drug_a") are auto-detected as factors when they have 2-20 unique values
- **Reference level selector** — In ANOVA mode, a dropdown lets you choose which factor level is the reference category; default is first sorted value
- **Named post hoc comparisons** — Pairwise comparisons display original level names (e.g. `origin[Europe] vs origin[Japan]`)
- **Configurable font size** — New "Font size" setting (8–20 pt) in the Settings dialog with live preview; persisted across sessions
- **Save plots as JPG** — New "Save Plots as JPG" button in the result panel exports bar charts and power curves via PyQtGraph's ImageExporter
- Replication scripts include `preserve_factor_level_names=True` parameter
- New test: `test_info_button.py`

### Changed

- Documentation dialog now supports deep-linking to a specific page via `initial_page` parameter (used by info button popups)
- History entries display `[ANOVA]` tag when the analysis used ANOVA mode
- Result subtab names use model-type prefix (`A_FP`, `A_FSS` for ANOVA; `lm_FP`, `lm_FSS` for linear)
- In-app documentation pages updated (`model_tab.md`, `analysis_tab.md`, `results_tab.md`, `key_concepts.md`, `overview.md`)

## [0.1.1] — 2026-02-16

### Added

- **Theme system** — light, dark, and dark pink themes with live preview in settings; follows system color scheme by default (`theme.py`)
- **Update checker** — background check against GitHub Releases API on startup; dismissible banner when a newer version is available (`update_checker.py`, `update_banner.py`)
- **Linux desktop integration** — auto-installs XDG `.desktop` file and icon on first launch so the app shows up in application menus
- **Citation in exports** — CSV exports and replication scripts now include MCPower version and citation header
- **Theme-aware progress animation** — dark pink theme gets its own cat animation variant (`cat_dp.gif`)
- **Theme-aware script panel** — replication script display adapts colors to current theme
- New tests: `test_theme.py`, `test_update_checker.py`, `test_update_banner.py`, `test_script_generator.py` (citation test)

### Changed

- Media files reorganized into `mcpower_gui/media/` subdirectory (icons, cat animation)
- Settings dialog now includes a theme selector as the first option
- Smoke test (`--smoke-test`) now verifies theme initialization and updated resource paths
- PyInstaller spec updated for new media paths

## [0.1.0] — 2026-02-13

Initial release.

### Core

- Three-tab interface: **Model**, **Analysis**, **Results**
- Formula input with live parsing and debounced validation
- Variable type configuration — continuous, binary, factor with proportion editing and auto-detection from uploaded data
- Effect size editor with spinbox + slider per predictor, automatic factor dummy expansion
- Correlation editor — pairwise matrix with strict / partial / no preservation modes
- CSV data upload with auto-detected variable types and correlations

### Analysis

- **Find Power** — run power analysis for a given sample size
- **Find Sample Size** — sweep over a range of sample sizes to find required N
- Configurable: simulations (OLS & mixed models), alpha, target power, seed, max failed simulations, parallel execution
- Scenario analysis (optimistic / realistic / doomer) with heterogeneity, heteroskedasticity, correlation noise, and distribution change parameters
- Per-run settings: correction method (Bonferroni, etc.), target tests, test formula
- Sample-size range input validation

### Results

- Power bar chart (PyQtGraph)
- Power curve plot (PyQtGraph)
- Results table with CSV export
- Replication script generation — standalone Python script that reproduces the analysis

### Application

- Background threading with cancellation support (`AnalysisWorker` / `QThread`)
- Progress dialog with animated cat and progress bar
- Analysis history — JSON persistence with browse and restore (History dialog)
- Settings dialog for simulation parameters and scenario configuration
- In-app documentation viewer (reads bundled Markdown files)
- Acknowledgments dialog
- Menu bar: Settings, History, Acknowledgments, Documentation, Support (opens GitHub)
- PyInstaller build spec for Windows, macOS, and Linux
- GitHub Actions build workflow
- Smoke test entry point (`--smoke-test`)

### Added in follow-up commits (pre-release)

- Test suite: `test_state.py`, `test_history_manager.py`, `test_resources.py`, `test_script_generator.py`, `test_smoke.py`
- GitHub Actions CI test workflow
- GPL-3.0 license
- README with feature overview and installation instructions
- Linux compatibility fixes
