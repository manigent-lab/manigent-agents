# Learnings index

Field knowledge for building and auditing DCF, 3-statement, LBO and comps models, sourcing inputs from SEC XBRL, Damodaran and the US Treasury curve, as of 2026-10-11. For any rate, date, tag, endpoint or effective date, trust the topic page over recollection, then open the page it links. Each page is a verbatim slice of the pool's field-knowledge file, listed here in file order.

## Topic pages (open the one whose consult-when matches)

1. [facts-a-generalist-gets-wrong.md](facts-a-generalist-gets-wrong.md) — setting a discount rate, pulling XBRL data, or modelling post-2025 US tax and disclosure changes. Start here: 13 dated facts with links.
2. [sec-edgar-apis.md](sec-edgar-apis.md) — writing any code that hits data.sec.gov (endpoints, CIK format, frames period codes, fair-access rules).
3. [xbrl-dedupe-and-periods.md](xbrl-dedupe-and-periods.md) — turning companyfacts JSON into a clean time series (dedupe key, period length, Q4 derivation, units, scale, signs).
4. [us-gaap-tag-mapping.md](us-gaap-tag-mapping.md) — mapping XBRL concepts onto model line items (revenue fallbacks, NCI, shares, D&A, capex, SBC, debt, extension tags).
5. [asu-standards-changes.md](asu-standards-changes.md) — a forecast depends on line-item granularity, tax footnotes, segment data or capitalization policy (ASUs 2023-07 through 2026-02).
6. [obbba-tax-in-models.md](obbba-tax-in-models.md) — forecasting cash taxes, deferred taxes, interest deductibility or capex timing for US entities (bonus depreciation, §174A, §163(j)).
7. [wacc-inputs.md](wacc-inputs.md) — building or auditing a discount rate (riskfree, ERP variants, beta unlever/relever, cost of debt, weights, CRP).
8. [dcf-conventions.md](dcf-conventions.md) — discounting, computing terminal value or reconciling FCF definitions (mid-year, stub, TV discounting, SBC, leases, NOLs).
9. [ev-to-equity-bridge.md](ev-to-equity-bridge.md) — converting EV to per-share value or EV comps (bridge items, TSM, RSUs, convertibles, share-count circularity).
10. [three-statement-linkage-and-audit.md](three-statement-linkage-and-audit.md) — building or reviewing an integrated model (core links, interest circularity, audit checklist, openpyxl recalc).
11. [lbo-mechanics.md](lbo-mechanics.md) — building a leveraged buyout model (sources and uses, fees, debt schedule, sweep, MOIC/IRR/XIRR, §163(j) check).
12. [data-gaps-and-sources.md](data-gaps-and-sources.md) — deciding which reference data may be shipped or must only be linked, checking whether a question lands in a known gap, or finding the primary source behind a fact.

## Reference data and tools

- `knowledge/treasury-par-yield-curve-2026.csv` — US Treasury daily par yield curve, 2026 year to date (fetched 2026-10-11; last row 2026-10-09). See `knowledge/treasury-par-yield-curve-README.md`. Offline fallback only: with web access on, fetch the rate for the valuation date with the `market-inputs` skill.
- Skills: `market-inputs` (point-in-time Treasury par yield and Damodaran ERP, with provenance), `edgar-facts` (companyfacts fetch + dedupe + 3-statement history), `model-auditor` (balance / cash / roll-forward ties, hard-code and formula-consistency scan), `dcf-validator` (DCF-specific sanity checks on a workbook), `valuation-calc` (WACC, discounting, TV, EV bridge, TSM, LBO returns), `xlsx-io` (openpyxl conventions).
