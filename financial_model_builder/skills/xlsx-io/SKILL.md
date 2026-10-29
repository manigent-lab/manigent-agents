---
name: xlsx-io
description: Read client workbooks into Python and write financial models to .xlsx with openpyxl - live formulas instead of computed numbers, inputs separated on an Inputs tab, blue/black/green colour code, sourced inputs, a Checks tab, documented iteration setting, then recalculation before anything reads values back. Use whenever an input or requested output is an .xlsx file.
---

<!-- Conventions adapted from the xlsx-author and dcf-model skills in
     anthropics/financial-services (plugins/agent-plugins/model-builder/skills/,
     Apache-2.0, Copyright Anthropic, PBC) at commit 574ed3624aebd0418c7e96cd101262f30210ab26.
     Modified by Manigent Contributors (2026-10-11): rewritten for this agent's sandbox,
     managed-agent output paths and Office-add-in branches removed, reading and
     recalculation sections added. -->

# xlsx in and out (openpyxl)

`openpyxl` (MIT) is the library; if it is missing, `pip install openpyxl`. Use the `csv`
module for CSV.

## Reading

```python
from openpyxl import load_workbook
wb_f = load_workbook(path)                  # formulas as text
wb_v = load_workbook(path, data_only=True)  # cached values (None if never calculated)
```
- Read both: formulas tell you how the model works, values what it says.
- `None` in `data_only` for a formula cell means the file was never recalculated: do not
  treat it as zero.
- Note the units row ("in thousands") and the period header (fiscal vs calendar) before
  using any number.

## Writing a model

- **Formulas, not results.** Every projection, discount factor, PV and sensitivity cell is
  an Excel formula string (`ws["D20"] = "=D19*(1+$C$8)"`). Only raw historicals,
  assumption drivers and market data are typed numbers.
- **Inputs tab.** Every driver lives once on an Inputs (or Assumptions) sheet and is
  referenced, never retyped. Add a cell comment with the source and date for each input,
  or mark it `[ASSUMPTION]`.
- **Colour code.** Blue font = typed input, black = formula, green = link to another
  sheet. Apply it as cells are written.
- **Plan the rows first.** Fix the row of every section before writing formulas, so
  references do not drift.
- **Checks tab.** Balance check, cash tie and roll-forward differences per period, each
  should be zero, plus one master cell that is TRUE only if all are.
- **Circularity.** If interest is on average balances, add a switch cell (circ on/off)
  and write on the cover that iterative calculation must be enabled; otherwise compute
  interest on opening balances.
- **Sensitivity tables.** Odd number of rows and columns, centre cell equal to the base
  case; each cell a full formula, not an approximation.
- Number formats: `'#,##0;(#,##0)'` amounts, `'0.0%'` rates, `'0.0x'` multiples; freeze
  panes under the header; one model per file.

## Recalculate, then verify

openpyxl does not calculate. Before reading values back or handing the file over:

```bash
soffice --headless --calc --convert-to xlsx --outdir recalculated/ model.xlsx
```

Then run `model-auditor` (and `dcf-validator` for a DCF) on the recalculated copy. If no
recalculation engine is available, say so and report the key outputs computed in Python
alongside the file.
