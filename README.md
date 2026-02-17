![Windows](https://img.shields.io/badge/Windows-0078D6?logo=windows&logoColor=white)
![macOS](https://img.shields.io/badge/macOS-000000?logo=apple&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?logo=linux&logoColor=black)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.16502734-blue)](https://doi.org/10.5281/zenodo.16502734)

```
███╗   ███╗  ██████╗ ██████╗ 
████╗ ████║ ██╔════╝ ██╔══██╗ ██████╗ ██╗    ██╗███████╗██████╗ 
██╔████╔██║ ██║      ██║  ██║██╔═══██╗██║    ██║██╔════╝██╔══██╗
██║╚██╔╝██║ ██║      ██████╔╝██║   ██║██║ █╗ ██║█████╗  ██████╔╝
██║ ╚═╝ ██║ ██║      ██╔═══╝ ██║   ██║██║███╗██║██╔══╝  ██╔══██╗
██║     ██║ ╚██████╗ ██║     ╚██████╔╝╚███╔███╔╝███████╗██║  ██║
╚═╝     ╚═╝  ╚═════╝ ╚═╝      ╚═════╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝
```

# MCPower GUI

MCPower GUI is a desktop application for **Monte Carlo power analysis**. It provides a graphical interface to the [MCPower](https://github.com/pawlenartowicz/MCPower) library, letting you plan sample sizes and estimate statistical power for complex study designs — without writing any code.

## Download

| Platform | Link |
|---|---|
| **Windows** | [MCPower.exe](https://github.com/pawlenartowicz/mcpower-gui/releases/latest/download/MCPower.exe) |
| **Linux** | [MCPower-linux](https://github.com/pawlenartowicz/mcpower-gui/releases/latest/download/MCPower-linux) |
| **macOS** | [MCPower-macos](https://github.com/pawlenartowicz/mcpower-gui/releases/latest/download/MCPower-macos) |
| **if above do not work** |[SourceForge](https://sourceforge.net/projects/mcpower/)|

No Python installation required — these are standalone executables.

### Windows

1. Download `MCPower.exe`.
2. Double-click to run.

**Note:** Windows SmartScreen may show a warning ("Windows protected your PC") because the application is not code-signed. Code signing certificates cost ~$100/year, which is not feasible for a free open-source project. The app is safe — you can verify the source code in this repository. To proceed: click **More info** → **Run anyway**.

Your antivirus software may also flag the file. This is a known false positive caused by the packaging tool (PyInstaller) used to create standalone Python executables. Many legitimate open-source applications trigger the same warning.

### Linux

1. Download `MCPower-linux`.
2. Open a terminal in the download folder:
   - **File manager:** Right-click in the folder → **Open Terminal Here**
   - **Or manually:** open a terminal and run `cd ~/Downloads`
3. Make the file executable and run it:
   ```bash
   chmod +x MCPower-linux
   ./MCPower-linux
   ```

### macOS

1. Download `MCPower-macos`.
2. Open Terminal in the download folder:
   - Open **Finder** → navigate to the Downloads folder → right-click the folder in the sidebar → **Services** → **New Terminal at Folder**
   - **Or manually:** open Terminal and run `cd ~/Downloads`
3. Make the file executable:
   ```bash
   chmod +x MCPower-macos
   ```
4. Run the app: right-click `MCPower-macos` in Finder → **Open** (required on first launch to bypass Gatekeeper, since the app is not signed with an Apple Developer certificate).

Full documentation is available in-app via the **Documentation** menu item.

## What is power analysis?

Statistical power is the probability that a study will detect a real effect when one exists. A power analysis helps you determine:

- **Find Power:** Given a sample size, what is the probability of detecting your expected effects?
- **Find Sample Size:** What sample size do you need to achieve a target power level (e.g., 80%)?

## Why Monte Carlo simulation?

Traditional power formulas work for simple designs but break down with interactions, correlated predictors, categorical variables, or non-normal data. MCPower uses **Monte Carlo simulation** — it generates thousands of synthetic datasets under your assumptions, fits the statistical model to each, and counts how often the effects are detected. This approach handles arbitrary complexity.

## Why MCPower?

**Just type your formula.** Enter your model the way you'd write it in R or a stats textbook — `outcome = treatment + covariate + treatment*covariate`. MCPower handles everything else: parsing the formula, setting up the simulation, and managing interactions and factor coding. No programming required. More model types (logistic regression, ANOVA) are coming soon.

**Scenarios show you the full picture.** Real studies rarely match textbook conditions — effect sizes may be smaller than expected, distributions may be skewed, or variance may not be constant. One checkbox enables automatic robustness testing. MCPower runs your analysis under optimistic, realistic, and worst-case conditions, so instead of a single number you get a range that shows how sensitive your design is to violated assumptions.

**Upload your data, skip the guesswork.** Drop in a CSV and MCPower auto-detects variable types (continuous, binary, or categorical), preserves real distributions, and handles correlations between predictors. String columns (e.g. "control", "drug_a", "drug_b") are supported and auto-detected as factors. Factor levels use the original values from your data — so `cyl` with values [4, 6, 8] shows up as `cyl[4]`, `cyl[6]`, `cyl[8]` instead of abstract indices. No need to manually specify whether each variable is normal, skewed, or categorical — MCPower samples from the empirical distribution. This is especially useful when you have pilot data or a related dataset and want your power analysis to reflect actual conditions.

## App workflow

1. **Model tab** — Define your study design: enter a formula, set variable types, specify effect sizes, and optionally upload empirical data with correlations.
2. **Analysis tab** — Choose analysis mode (Find Power or Find Sample Size), set target power, enable scenarios, and select multiple testing corrections.
3. **Results tab** — View power tables, bar charts, power curves, scenario comparisons, and a replication script you can run independently.

## Formula syntax

MCPower uses R-style formula notation:

| Formula | Meaning |
|---|---|
| `y = x1 + x2` | Two main effects |
| `y = x1 + x2 + x1:x2` | Two main effects + interaction |
| `y = x1 * x2` | Shorthand for `x1 + x2 + x1:x2` |
Both `=` and `~` are accepted as separators between the dependent variable and predictors.

**Note:** Mixed-effects models (e.g., `y ~ x + (1|school)`) are supported by the MCPower library but are not yet available in the GUI. Mixed model support in the app is planned for a future release.

## Built on

MCPower GUI is built on [MCPower](https://github.com/pawlenartowicz/MCPower).

## License & Citation

GPL v3. If you use MCPower in research, please cite:

Lenartowicz, P. (2025). MCPower: Monte Carlo Power Analysis for Statistical Models. Zenodo. DOI: 10.5281/zenodo.16502734

```bibtex
@software{mcpower2025,
  author = {Pawel Lenartowicz},
  title = {MCPower: Monte Carlo Power Analysis for Statistical Models},
  year = {2025},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.16502734},
  url = {https://doi.org/10.5281/zenodo.16502734}
}
```

## Support

This project is free and open-source. If you'd like to support its development, donations are appreciated!

[Support this project](https://freestylerscientist.pl/support_me)
