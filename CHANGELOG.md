# Changelog

All notable changes to MCPower GUI are documented in this file.

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
