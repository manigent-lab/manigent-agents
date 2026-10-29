---
name: market-inputs
description: Fetch a point-in-time riskfree rate (US Treasury daily par yield curve, any tenor) and Damodaran implied equity risk premium (any named variant) for a valuation date, each stamped with the date inside the data, its series name and source URL, plus a same-series check between the two. Use whenever a WACC, cost of equity, discount rate or "current" Treasury yield or ERP is needed - never quote one from memory or a static table. Works offline on a saved CSV / xlsx; the network mode is refused when MANIGENT_WEB_DISABLED=1.
---

# market-inputs

Rates go stale on the next Treasury print or Damodaran update, so this agent never quotes a
remembered one. It fetches the value **for the valuation date** and carries its provenance
into the answer.

```bash
H="$MANIGENT_AGENT_DIR/personal-skill-hub/skills/market-inputs/market_inputs.py"
```

## Commands

| Need | Command |
|---|---|
| Riskfree rate for a valuation date | `python3 $H treasury --as-of YYYY-MM-DD [--tenor 10y]` |
| ERP for a valuation date | `python3 $H erp --as-of YYYY-MM-DD [--variant headline]` |
| Both, with the same-series check | `python3 $H wacc-inputs --as-of YYYY-MM-DD [--tenor 10y] [--variant headline]` |
| Offline, on a file the user gave | add `--csv saved.csv` / `--xlsx ERPbymonth.xlsx` |

Tenors: `1m 2m 3m 4m 6m 1y 2y 3y 5y 7y 10y 20y 30y`. ERP variants: `headline` (Damodaran's
T12m with sustainable payout, the figure on his home page), `t12m` (trailing 12-month cash
yield), `t12m-adj-riskfree`, `smoothed` (10-year average), `normalized`, `net-cash-yield`.

## Reading the answer

- `value` is a decimal (`0.0414` = 4.14%). `as_of` is the date the value is **for**:
  the Treasury observation day, or the month Damodaran's figure starts. `requested_as_of`
  is what you asked for. Quote `as_of`, not today.
- `last_modified` is when the file last changed on the server. It is **not** the data
  date: Damodaran's yearly files are edited long after their data date.
- `riskfree_used` is the 10-year rate Damodaran computed that month's ERP against.
- A month's ERP is published in its first days, so `--as-of` on the 1st can return a
  figure that was not yet public that morning. For a valuation dated the 1st, consider the
  prior month and say which you used.

## Rules

1. **Point in time.** Pass the valuation date as `--as-of`. A 2026-09-30 valuation uses the
   September 2026 ERP even if October's is already out. Use "latest" only when the user
   asks for today's value, and then say the date.
2. **Name the variant** in the answer ("Damodaran implied ERP, T12m with sustainable
   payout, 2026-09-01: 4.14%"). If the user names a variant, use it.
3. **Same series.** The check runs only for `--tenor 10y`, the tenor Damodaran uses. If `wacc-inputs` warns, either pair the ERP with `riskfree_used`, or
   keep the Treasury rate and say in one line why you mix them.
4. **No market-standard defaults.** A 5.0-6.0% ERP "market standard" (as in the free
   Anthropic DCF skill) is not an input. Replace it with this fetch.
5. **Web off:** with `MANIGENT_WEB_DISABLED=1` use `--csv` / `--xlsx` on a file you were
   given, or `knowledge/treasury-par-yield-curve-2026.csv`, and say the value is as of
   that snapshot's last date.

Exit status 2 with `error:` on stderr means no observation fits (date before the data,
unknown tenor or variant, or the workbook layout changed). Say so; never fill the gap.
