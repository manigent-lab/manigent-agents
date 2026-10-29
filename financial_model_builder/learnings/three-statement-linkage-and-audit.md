## 3-statement linkage, circularity and model audit
**Consult when:** building or reviewing an integrated model.
- **Core links:** NI → retained earnings and CFO; D&A and SBC added back; ΔNWC from BS deltas (asset increases negative); PP&E roll (beginning + capex − D&A − disposals); debt roll-forward → CFF; ending cash = beginning + CFO + CFI + CFF = BS cash; assets − liabilities − equity = 0 every period.
- **Interest circularity:**
  - Interest on average balances creates a loop: interest → NI → cash → debt paydown → interest.
  - Options: enable iterative calculation (defaults 100 iterations / 0.001), compute interest on beginning balances, or use a copy-paste macro.
  - Always add a circuit breaker: a switch cell that sets interest to zero or beginning-balance mode, so #REF!/#NUM! errors don't propagate through the loop permanently.
  - Document the iterative-calc setting on the cover sheet, because a recipient's Excel may have it off.
- **Audit checklist:** balance check zero every period; CF cash ties to BS cash; no hard-codes in forecast columns (Go To Special → Constants, or scan formula cells for numeric literals); consistent formulas across rows (R1C1 diff); capex and repayments negative in CF; no external links; consistent units (thousands vs millions vs full-value XBRL); FY vs calendar alignment; tax applied to EBT; retained-earnings roll ties; shares tie to the TSM output; historicals tie to filed 10-K; circular switch documented.
- **Python builds:** openpyxl writes formulas but does not calculate them. Recalculate with LibreOffice headless or Excel before reading values.

