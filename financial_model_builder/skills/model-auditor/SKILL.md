---
name: model-auditor
description: Audit an integrated financial model (3-statement, DCF, LBO, comps) in .xlsx or CSV - balance check every period, CF cash ties to BS cash, cash continuity, retained-earnings / PP&E / debt roll-forwards, D&A and capex consistency, plus a workbook scan for error values, uncalculated formulas, hard-coded literals, pasted-over values, inconsistent row formulas, external links, hidden sheets and circular references with the iterative-calc setting. Use for "audit / check / QA this model", "model won't balance", "something's off", or before sending any model on.
---

<!-- Adapted from the audit-xls skill in anthropics/financial-services
     (plugins/agent-plugins/model-builder/skills/audit-xls/SKILL.md, Apache-2.0,
     Copyright Anthropic, PBC) at commit 574ed3624aebd0418c7e96cd101262f30210ab26.
     Modified by Manigent Contributors (2026-10-11): rewritten around a scripted
     checker (model_auditor.py), scope question and Office-specific steps removed,
     checklist trimmed and merged with the pool's linkage and circularity rules. -->

# model-auditor

Balance first: if the balance sheet does not balance, quantify the gap per period and
trace it before anything else; every downstream number is suspect until it does.

```bash
H="$MANIGENT_AGENT_DIR/personal-skill-hub/skills/model-auditor/model_auditor.py"
python3 $H all  --xlsx model.xlsx --format table            # ties + formula scan
python3 $H ties --csv statements.csv --format table         # CSV export of the statements
python3 $H scan --xlsx model.xlsx --sheet DCF --allow-literals 0,1,12
```

## 1. Prepare

- **Recalculate first.** A workbook written by openpyxl has formulas but no cached
  values. If the scan reports `not_calculated`, recalculate (LibreOffice headless
  `soffice --headless --convert-to xlsx`, or Excel) and audit the recalculated copy.
- Ties read rows by label (first text column; one numeric column per period, left to
  right). If a row is missed, the `coverage` line says which checks did not run: pass
  `--map "bs_cash=Cash & equivalents,cf_ending_cash=Cash, end of year"`. Keys: see
  `ALIASES` in the script, plus `is_d_and_a`, `cf_d_and_a`, `cf_capex`.
- Limit to the statement sheets with `--sheet` when other tabs repeat the same labels.
- `--tol` is in model units (default 0.5): raise it for a model in millions with rounding.

## 2. What the checks mean

| Check | Severity | Usual cause |
|---|---|---|
| balance | critical | a BS line not linked to the CF, or a CF line with no BS counterpart |
| cash_tie / cf_sum / cash_continuity | critical | ending cash typed, a CF subtotal missing a line, opening cash not linked |
| re_roll | critical | dividends or buybacks booked elsewhere, NI not linked |
| ppe_roll | warning | D&A includes intangible amortization, disposals missing |
| debt_roll | critical | repayments not equal to the debt schedule |
| da_match / capex_sign | warning | IS and CF D&A differ; capex entered positive on the CF |
| error_value | critical | #REF!/#DIV/0!/... in a cached value |
| hardcode_in_formula / pasted_value | warning | a growth rate or plug typed inside a formula or over one |
| inconsistent_formula | warning | a cell breaks its row's relative pattern (the first forecast column often legitimately differs: check, don't auto-fix) |
| external_link / hidden_sheet | warning | values that can change or hide outside the file |
| circular_reference | critical if iterative calc is off, info if on | interest on average debt; make sure a switch breaks the loop and the cover documents the setting |

Then read the model for what a script cannot see (from `memory/learnings/three-statement-linkage-and-audit.md`
and `dcf-conventions.md`): units (thousands vs millions vs full-value XBRL), FY vs calendar
alignment, tax on EBT, shares tied to the TSM output, historicals tied to the filed 10-K,
TV share of EV, growth above WACC or the riskfree rate, mid-year vs end-year mixing inside
one sensitivity table, unlevered FCF that includes interest, book instead of market weights.
For DCF workbooks also run `dcf-validator`.

## 3. Report

Lead with one line: model type, overall (Clean / Minor issues / Major issues) and counts.
Then a findings table: # | Sheet | Cell/Range | Severity | Check | Issue | Suggested fix.
Report first; change the workbook only when asked.
