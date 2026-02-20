# Data Preparation

This guide explains how to prepare your data file for upload into MCPower GUI.

## File format

MCPower GUI accepts **CSV (comma-separated values)** files. Most spreadsheet applications (Excel, Google Sheets, LibreOffice Calc) can export to CSV.

## Requirements

- **Use comma separators** (not semicolons or tabs).
- **Include a header row** with column names as the first row.
- **Have consistent data types per column** — don't mix numbers and text in the same column.
- **Avoid special characters in column names** — stick to letters, numbers, and underscores.
- **Have no missing values or empty cells** — fill or remove incomplete rows before uploading.
- **Use UTF-8 encoding** (most editors default to this).

## What happens when you upload

- **Numeric columns** are auto-converted to numbers and used as-is.
- **Non-numeric columns** (e.g. "control", "drug_a", "drug_b") are kept as strings and treated as factor variables.
- **Columns named "" or starting with "Unnamed"** (common index columns from spreadsheet exports) are automatically skipped.

## Variable type detection

MCPower auto-detects variable types based on the number of unique values in each column:

| Unique values | Detected type |
|---|---|
| 2 | Binary |
| 3–6 | Factor |
| 7+ | Continuous |

String columns with 2–20 unique values are always detected as factors.

## Factor levels and reference categories

When a column is detected as a factor, MCPower uses the **original values** from your data as level names. For example:

- A column `cyl` with values [4, 6, 8] produces dummies `cyl[6]` and `cyl[8]`, with `cyl[4]` as reference.
- A column `origin` with values ["Europe", "Japan", "USA"] produces `origin[Japan]` and `origin[USA]`, with "Europe" as reference.

The **first sorted value** is the default reference level (alphabetically for strings, numerically for numbers). In ANOVA mode, you can change the reference level with a dropdown selector.

## Tips

- Only include columns you plan to use in your model (predictors and the dependent variable is optional).
- If your data has an ID or index column, either remove it or ensure it starts with "Unnamed" so it's skipped automatically.
- Check that factor columns don't have typos or inconsistent capitalization (e.g. "Male" vs "male" would be treated as two different levels).
