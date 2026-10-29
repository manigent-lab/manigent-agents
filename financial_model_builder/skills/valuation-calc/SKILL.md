---
name: valuation-calc
description: Stdlib Python functions for the arithmetic in DCF, WACC, EV-to-equity and LBO work - CAPM with CRP, beta unlever/relever and cash correction, after-tax cost of debt with disallowed interest, market-value WACC, end-year / mid-year / stub discount exponents, unlevered FCF, Gordon and exit-multiple terminal values with explicit TV timing, terminal sanity flags, the EV-to-equity bridge, treasury-stock and if-converted dilution solved as a fixed point, IRR / XIRR (actual/365) / MOIC, sources and uses with the sponsor-equity plug, a 30%-of-ATI interest limit with carryforward, and a multi-tranche debt schedule with mandatory amortization, PIK and cash sweep. Use whenever a valuation or LBO number has to be computed rather than estimated.
---

# valuation-calc

Every convention is an argument, so the choice is visible next to the number:
discount `timing` ('end' | 'mid'), `stub`, TV `method` and `gordon_discounting`,
`interest_basis` ('beginning' | 'average'). Rates are decimals.

```bash
H="$MANIGENT_AGENT_DIR/personal-skill-hub/skills/valuation-calc/valuation_calc.py"
python3 $H list                                   # every function with its signature
python3 $H <function> '<JSON keyword arguments>'
python3 $H <function> @args.json
```

or `sys.path.insert(0, "<that folder>"); import valuation_calc as vc` in a script.

| Task | Function(s) |
|---|---|
| Cost of equity | `capm(rf, beta, erp, crp=0, crp_exposure=1)` |
| Beta | `unlever_beta`, `cash_corrected_beta`, `relever_beta` (market D/E, marginal rate) |
| Cost of debt | `after_tax_cost_of_debt(pre_tax, marginal_tax_rate, deductible_share=1)` |
| WACC | `wacc(equity_value, debt_value, cost_of_equity, after_tax_cost_of_debt, ...)` |
| Discounting | `discount_exponents` / `discount_factors` / `present_value(..., prorate_first=)` |
| FCF | `unlevered_fcf(ebit, tax_rate, d_and_a, capex, delta_nwc, cash_taxes=None)` |
| Terminal value | `gordon_terminal_value`, `exit_multiple_terminal_value`, `terminal_exponent`, `terminal_checks` |
| EV to equity | `equity_bridge(ev, items)`, `treasury_stock_shares`, `diluted_value_per_share` |
| Returns | `irr`, `xirr`, `npv`, `moic`, `exit_equity` |
| LBO | `sources_and_uses`, `debt_schedule`, `interest_limit_163j` |

Rules the functions enforce or expect (details in `memory/learnings/`):
- `terminal_exponent(method="exit")` is always the end of period N. For Gordon you must
  pass `gordon_discounting` ('end' or 'mid'); 'mid' is allowed only with mid-year flows.
- `equity_bridge` takes positive magnitudes and a fixed sign per item; include
  `operating_leases` only when lease cost is out of the cash flows, and `nol_value` only
  when NOLs are not already in the forecast.
- `diluted_value_per_share` expects equity value with converts already deducted as debt;
  an in-the-money convert is swapped (debt added back, shares added), never both.
- `debt_schedule(interest_basis="average")` solves the interest circularity by iteration;
  'beginning' avoids it. A shortfall shows as `revolver_need`, not as negative cash.
- `interest_limit_163j` takes ATI as you compute it; the post-2024 US base adds D&A back.

State the inputs, the conventions and the result; show the formula once if the user
needs to check it. Run the arithmetic here rather than by hand for anything multi-step.
