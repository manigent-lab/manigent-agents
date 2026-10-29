---
name: edgar-facts
description: Pull a US filer's XBRL facts from SEC EDGAR (companyfacts, companyconcept, frames, submissions, ticker-to-CIK) and normalise them into a deduped time series or a 3-statement history - one value per data period, latest filing wins, period length from dates not fy/fp, Q4 derived for flow items, units never mixed, tag fallbacks stitched. Use whenever historicals, share counts or peer data come from SEC filings, or when a user hands you a companyfacts JSON. Works offline on a saved JSON; the network mode is refused when MANIGENT_WEB_DISABLED=1.
---

# edgar-facts

Raw companyfacts is not a time series. The same period appears once per filing that
repeats it, `fy`/`fp` describe the filing rather than the data, a 10-Q holds both the
3-month and the year-to-date fact under one `fp`, and there is usually no Q4 fact at all.
This helper applies the rules in `memory/learnings/xbrl-dedupe-and-periods.md` and the
tag fallbacks in `memory/learnings/us-gaap-tag-mapping.md` so you never do it by hand.

```bash
H="$MANIGENT_AGENT_DIR/personal-skill-hub/skills/edgar-facts/edgar_facts.py"
```

**Web off means offline only.** If `MANIGENT_WEB_DISABLED=1` is set, web access is off,
or the task says you cannot browse, do not call `fetch` / `cik` without `--tickers-file`,
`curl`, `http-api` or any other route to sec.gov. Work on the JSON the user gave you; if
there is none, say which filing data you would need.

## 1. Get the data (web allowed only)

1. Ticker to CIK: `python3 $H cik --ticker <TICKER> --user-agent "<Org> <contact e-mail>"`.
   Never pass a ticker to a data.sec.gov endpoint.
2. `python3 $H fetch companyfacts --cik <CIK> --out cf.json --user-agent "<Org> <e-mail>"`
   (or set `SEC_USER_AGENT`). The script refuses without an e-mail in the User-Agent,
   sends `Accept-Encoding: gzip, deflate` and spaces requests under SEC's 10/s ceiling
   across every concurrent run on this computer (a stamp file in `$AGENT_SHARED_STORAGE_DIR`,
   overridable with `EDGAR_THROTTLE_FILE`).
   Use the operator's or the user's contact, never an invented address.
3. Other endpoints: `fetch concept --cik --tag`, `fetch submissions --cik`,
   `fetch frames --tag <Tag> --unit <unit> --period CY####|CY####Q#|CY####Q#I`.
   Balance-sheet items need the `I` (instant) period. Write the unit as companyfacts
   shows it (`USD/shares`); the script converts it to the frames form (`USD-per-shares`).

Record the fetch date next to every number you take from it.

## 2. Find the concepts

`python3 $H tags --facts cf.json --grep <word>` lists concepts with their units, counts and
date range. If a standard tag is missing, the line is probably under a company extension
or only a dimension member (segments): say so, never impute it.

## 3. Build the series

| Need | Command |
|---|---|
| One concept, one row per period | `series --facts cf.json --tag <Tag> [--unit U] [--period annual\|quarterly\|ytd\|instant]` |
| Calendar-aligned (frame) values | add `--mode frame` |
| Quarterly flows with Q4 filled | `series ... --period quarterly --derive-q4` |
| Normalised history, long format | `history --facts cf.json [--freq annual\|quarterly]` |
| Same, line items x period ends | `history ... --wide` |

Options: `--forms 10-K,10-Q` (default: 10-K/10-Q/20-F/40-F and their amendments; `all`
keeps 8-K exhibits too), `--format csv|json`, `--out file`.

What the output means:
- `start`/`end` are the **data period**; `filing_fy`/`filing_fp` (or `fy`/`fp` in `series`)
  are the filing's labels, kept only for tracing. Label model columns by period end.
- `derived` is set on computed Q4 rows (FY minus 9-month YTD, else FY minus Q1-Q3).
  Q4 is never derived for EPS, share counts or balance-sheet items.
- `tag` shows which fallback filled each period (revenue stitches newest tag first).
- `dei:EntityCommonStockSharesOutstanding` sums the per-class rows of one filing; it is
  the cover-page date's count, not a period-end or average count.
- Values are full units and the concept's natural sign (capex positive). Convert to the
  model's units and signs in the model, and say so.
- A stderr `warning: conflicting values in one filing` means two facts disagree inside
  one accession: check the filing before using that period.

## 4. Before using the numbers

- Tie the history to the filed statements for at least one year (revenue, net income,
  total assets, cash). XBRL errors and restatements happen.
- `net_income` is attributable to the parent (use it for EPS and the bridge);
  `net_income_incl_nci` includes NCI.
- Debt lines are listed separately: decide whether current maturities sit inside the total
  you take, so they are not counted twice, and treat leases consistently with EBITDA.
