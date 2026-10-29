# treasury-par-yield-curve-2026.csv

US Treasury **Daily Treasury Par Yield Curve Rates** for calendar 2026, as published
by the US Department of the Treasury. The file is the unmodified CSV download.

- **Fetched:** 2026-10-11 (UTC), from
  `https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2026/all?type=daily_treasury_yield_curve&field_tdr_date_value=2026&page&_format=csv`
- **Coverage:** 195 business days, 2026-01-02 to 2026-10-09 (newest row first).
- **SHA-256:** `0e7164f6f348497a4541b61ce9b3e76fc00902c988540d08332a7d956350c764`
- **Licence:** US government work, public domain (17 USC 105).
- **Viewer page:** https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve

## Columns

`Date` (MM/DD/YYYY), then par yields in percent (bond-equivalent, semiannual
compounding) for the tenors `1 Mo`, `1.5 Month`, `2 Mo`, `3 Mo`, `4 Mo`, `6 Mo`,
`1 Yr`, `2 Yr`, `3 Yr`, `5 Yr`, `7 Yr`, `10 Yr`, `20 Yr`, `30 Yr`.

## Use

- A riskfree rate is an observation on a date: quote the tenor, the value and the
  `Date` row it came from. Match the tenor to the ERP series you pair it with
  (see `memory/learnings/wacc-inputs.md`).
- These are **par** yields, not zero-coupon (spot) rates. Bootstrapping a spot curve
  for discounting dated flows is a separate step; say so if you do it.
- The snapshot ends 2026-10-09. When web access is allowed, re-download the same URL
  for later dates; when it is not, say the rate is as of the last row.

Read it with the stdlib:

```python
import csv
rows = list(csv.DictReader(open(path, newline="")))
ten_year = {r["Date"]: float(r["10 Yr"]) for r in rows if r["10 Yr"]}
```
