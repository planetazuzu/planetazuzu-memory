---
name: xlsx
description: Handle spreadsheet files as primary input or output. Use for opening, reading, editing, or fixing .xlsx, .xlsm, .csv, or .tsv files (adding columns, computing formulas, formatting, charting, cleaning data); creating new spreadsheets from scratch; or converting between tabular formats. Do NOT use when the primary deliverable is a Word document, HTML report, standalone Python script, database pipeline, or Google Sheets API integration.
license: MIT
compatibility: opencode
---

## What I do

- Create Excel spreadsheets (.xlsx) from scratch with professional formatting
- Read, edit, and fix existing .xlsx, .xlsm, .csv, .tsv files
- Add columns, compute formulas, apply formatting, build charts
- Clean and restructure messy tabular data
- Convert between tabular formats (CSV ↔ XLSX, etc.)

## When to use me

Use when the deliverable is a spreadsheet file. Trigger when the user mentions a spreadsheet by name or path, or asks to clean/restructure tabular data.

Do NOT use when the deliverable is a Word doc, HTML report, Python script, or database pipeline.

## Quality standards

- **Professional font**: Use Arial or Times New Roman consistently unless instructed otherwise
- **Zero formula errors**: Deliver with ZERO `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, `#NAME?` errors
- **Preserve existing templates**: Match existing format/style exactly when modifying files — never impose new formatting on files with established patterns

## How I work

### Primary library: openpyxl (Python)

```bash
pip install openpyxl
```

```python
from openpyxl import Workbook, load_workbook

# Create new workbook
wb = Workbook()
ws = wb.active
ws.title = "Sheet1"

# Write data
ws["A1"] = "Name"
ws["B1"] = "Value"
ws.append(["Alice", 100])
ws.append(["Bob", 200])

wb.save("output.xlsx")
```

### Reading existing files

```python
wb = load_workbook("data.xlsx")
ws = wb.active

for row in ws.iter_rows(values_only=True):
    print(row)
```

### Formatting cells

```python
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Bold header
ws["A1"].font = Font(bold=True, name="Arial", size=12)

# Background color
ws["A1"].fill = PatternFill(fill_type="solid", fgColor="4472C4")

# Center align
ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

# Column width
ws.column_dimensions["A"].width = 20

# Row height
ws.row_dimensions[1].height = 30
```

### Formulas

```python
ws["C2"] = "=SUM(B2:B10)"
ws["D2"] = "=AVERAGE(B2:B10)"
ws["E2"] = "=IF(B2>100,\"High\",\"Low\")"
```

### Charts

```python
from openpyxl.chart import BarChart, Reference

chart = BarChart()
data = Reference(ws, min_col=2, min_row=1, max_row=10)
chart.add_data(data, titles_from_data=True)
ws.add_chart(chart, "E5")
```

### Working with CSV

```python
import csv
import openpyxl

wb = Workbook()
ws = wb.active

with open("data.csv", newline="") as f:
    reader = csv.reader(f)
    for row in reader:
        ws.append(row)

wb.save("output.xlsx")
```

### Using pandas for complex transformations

```bash
pip install pandas openpyxl
```

```python
import pandas as pd

df = pd.read_excel("input.xlsx")
df["new_column"] = df["value"] * 2
df.to_excel("output.xlsx", index=False)
```
