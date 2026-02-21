# Changelog

All notable changes to MCPower GUI are documented in this file.

## [0.2.4] — 2026-02-21

### Fixed

- **Factor:factor interaction expansion** — `_expand_predictors()` now produces Cartesian product of non-reference dummy levels (e.g. `a[2]:b[2]`, `a[3]:b[2]`) instead of incorrect partial expansion (`a:b[2]`, `a[2]:b`). Applies to both Linear formula and ANOVA modes
- Factor:factor interactions with named level labels now expand correctly (e.g. `origin[Japan]:cyl[6]` instead of `origin:cyl[6]`)
- Reference level placeholder rows no longer appear for interaction terms in the effects editor — only main effects show the disabled `(ref)` row

### Changed

- Bumped MCPower dependency to 0.5.3

## [0.2.3] — 2026-02-20

### Changed

- **Documentation system overhaul** — Split monolithic doc files (model_tab.md, analysis_tab.md, results_tab.md, settings.md) into ~20 per-section pages. Each info button now opens the full topic page instead of extracting a section at runtime
- **Documentation dialog redesign** — Sidebar now groups pages under section headers (Overview, Model, Analysis, Results, Other) with indented child pages and a custom styled delegate
- **Simplified InfoButton API** — Removed `extract_doc_section()` and section-heading-based extraction; `InfoButton` and `attach_info_button` take only a doc filename
- Expanded Key Concepts with wiki links, random slopes, and nested effects documentation
- New doc pages: Data Preparation, Mixed Models Guide, Citation
- Fixed GitHub URL in overview (`freestylerscientist` → `pawlenartowicz`)
- Tutorial guide: smaller dismiss button, more visible background
- Bumped MCPower dependency to 0.5.2

## [0.2.2] — 2026-02-20

### Fixed

- **macOS app opens in Terminal** — PyInstaller spec now produces a proper `MCPower.app` bundle (via `BUNDLE` step) so Finder treats it as a GUI application instead of handing it to Terminal
- **Version shown in Settings** — Settings dialog now displays the current app version (`__version__` imported from `mcpower_gui`)
- CI build workflow updated for macOS build targets

### Changed

- Build spec reads version from `pyproject.toml` automatically — no longer needs manual update when bumping the version
- Build spec bundles `mcpower-gui` package metadata so `importlib.metadata.version("mcpower-gui")` works in the frozen app
- Removed inaccurate note about mixed-effects models support from README

## [0.2.1] — 2026-02-20

### Fixed

- **Tutorial tips missing in frozen app** — `tips.yaml` was not included in the PyInstaller bundle; tips now load correctly in packaged builds
- **Offscreen crash in CI tests** — Added `tests/conftest.py` with a session-scoped `QApplication` fixture and `QT_QPA_PLATFORM=offscreen` so GUI tests run headlessly without a display

## [0.2.0] — 2026-02-20

### Added

- **Mixed model (LME) GUI support** — Formula input now parses random effects syntax (e.g. `(1|school)`, `(1 + treatment|school)`). Cluster Configuration section auto-appears with ICC, N clusters, slope variance, and slope-intercept correlation controls
- **Tutorial guide** — Contextual next-step guide above Model and Analysis tabs. Declarative YAML-driven tip engine (`tips.yaml`, `tip_engine.py`) evaluates state conditions to show relevant tips. Dismissible per session; re-openable from Settings
- **Tip engine** — Pure Python `TipEngine` class with AND-logic conditions supporting exact match, `!empty`, `!value`, `>=N` operators. `clusters_resolved` computed state key eliminates rule duplication
- **Variable buttons** — After CSV upload, clickable variable name buttons appear for quick insertion into the formula or ANOVA factors. Uses new `FlowWidget` wrapping layout
- **Wheel-scroll protection** — `WheelGuard` application-level event filter + `SpinBox`/`DoubleSpinBox` subclasses that ignore wheel input, preventing accidental value changes while scrolling
- **Cluster value preservation** — `ClusterEditor` preserves user-edited ICC/cluster values when the formula changes and cards are rebuilt
- New tests: `test_cluster_editor.py`, `test_tip_engine.py`, `test_tips_yaml.py`, `test_formula_input.py`, `test_mixed_model_integration.py`, `test_factor_autonaming.py`

### Changed

- **Pandas removed from GUI** — CSV reading now uses `csv.DictReader` + `numpy.corrcoef` instead of `pandas.read_csv`. Reduces binary size and startup time
- **Unified title widget positioning** — `TitleWidgetPositioner` (configurable `x_offset`) replaces both `_InfoPositioner` and `_DotPositioner`, reducing code duplication
- **AnovaFactorEditor public API** — Added `get_factor_names()`, `clear_factors()`, `notify_changed()`. External code no longer accesses private `_factor_rows`, `_clear_factor_rows()`, `_on_changed()`
- **FormulaInput public API** — `EXAMPLES` (was `_EXAMPLES`) and `load_example()` (was `_load_example()`) are now public
- **Tabs expose `reopen_tutorial()`** — Public method replaces direct access to private `_tutorial` attribute
- **Model type signal deduplication** — `model_type_changed` only emits when the type actually changes, via `_emit_model_type()` guard
- **Tips YAML deduplication** — Computed `clusters_resolved` state key eliminates 12 duplicate cluster/non-cluster rule pairs (642 → ~370 lines)
- CSV export uses `utf-8-sig` encoding for Excel compatibility on Windows
- New widget modules define `__all__` exports
- Results tab names now include formula prefix and analysis mode
- Updated in-app documentation (`model_tab.md`, `settings.md`, `overview.md`, `key_concepts.md`)
- CI workflows updated for mixed model test dependencies

### Fixed

- `_format_level_label` now guards against `float('inf')` with `math.isfinite()` check
- Module-level YAML loading in `tutorial_guide.py` wrapped in try/except — GUI starts even if `tips.yaml` is missing or malformed
- NaN check in `_get_eligible_columns` uses `math.isnan` instead of fragile `v != v` pattern
- `_close_others` reverse iteration documented for maintainability

## [0.1.2] — 2026-02-17

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
