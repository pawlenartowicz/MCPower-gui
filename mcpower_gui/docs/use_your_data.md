# Use Your Data (optional)

By default, MCPower **generates synthetic data** from your specifications (formula, variable types, effect sizes). This works well for most power analyses.

If you have an **empirical dataset**, you can upload it here. MCPower will then use your real data's structure instead of generating synthetic data. When data is uploaded:

- Variable types are **auto-detected** from the data (2 unique values = binary, 3-6 = factor, 7+ = continuous).
- **String columns** are supported — columns with non-numeric values (e.g. "control", "drug_a", "drug_b") are auto-detected as factors if they have 2-20 unique values.
- Factor levels use the **original values from the data** (e.g. `cyl` with values 4, 6, 8 produces dummies `cyl[6]`, `cyl[8]` with `cyl[4]` as reference).
- The first sorted value is the default **reference level** (alphabetically for strings, numerically for numbers). In ANOVA mode, you can change the reference level with a dropdown selector.
- Correlations between variables are computed from the data.
- The type dropdowns are locked to the detected types.

## CSV file requirements

The GUI reads CSV files using Python's built-in `csv` module. Your file should:

- **Use comma separators** (not semicolons or tabs).
- **Include a header row** with column names.
- **Have consistent data types per column** — don't mix numbers and text in the same column.
- **Avoid special characters in column names** — stick to letters, numbers, and underscores.
- **Have no missing values or empty cells** — fill or remove incomplete rows before uploading.
- **Use UTF-8 encoding** (most editors default to this).

Numeric columns are auto-converted to numbers. Non-numeric columns (e.g. "control", "drug_a") are kept as strings and treated as factors. Columns named "" or starting with "Unnamed" (common index columns from spreadsheet exports) are automatically skipped.

## Correlation mode

When data is uploaded, the correlation mode controls how data-derived correlations interact with your manual settings:

- **strict** — Data-backed variable pairs are locked to their empirical correlations. Pairs without data can be edited manually. If no data variables match, correlations are disabled entirely.
- **partial** (default) — Data correlations are computed and shown, but you can override any pair. Your overrides are merged on top of the data correlations.
- **no** — Data correlations are ignored. Only your manually entered correlations are used.
