## XBRL fact dedupe and period traps
**Consult when:** turning companyfacts JSON into a clean time series.
- Each fact carries `start` (duration facts only), `end`, `val`, `accn`, `fy`, `fp`, `form`, `filed` and sometimes `frame`. A 10-K repeats the prior two years of income-statement and cash-flow data and the prior-year balance sheet, so the same period appears in up to three filings (verified on Apple, 2026-10-11).
- Dedupe rule: key on (`start`, `end`) for duration facts or `end` for instants, then keep the row with the latest `filed`. That picks up restatements and recasts. Alternatively, keep only rows with `frame` for calendar-aligned series. Never key on `fy`.
- Classify period length from `end − start`, not from `fp`. A 10-Q contains both the 3-month and the year-to-date facts under the same `fp`.
- There is usually no Q4 duration fact. Derive Q4 as the FY value minus the 9-month YTD value, or minus the sum of Q1–Q3. Do this only for flow items. Balance-sheet Q4 is the FY instant.
- Amendments (10-K/A, 10-Q/A) and 8-K exhibits can also carry facts. Filter `form` to the set you trust.
- Units: `USD`, `shares`, `USD/shares` in companyfacts, `pure` for ratios. Foreign filers may report `EUR`, `CAD` and others in separate arrays. Do not sum across unit arrays.
- Scale: XBRL values are in units, not thousands. A filing that says "in millions" is still stored at full value.
- Signs: XBRL stores the natural balance of the concept. For example, `PaymentsToAcquirePropertyPlantAndEquipment` is positive even though it is a cash outflow. Apply the sign in the model, not in the extract.

