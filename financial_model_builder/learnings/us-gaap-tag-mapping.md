## us-gaap tag mapping and fallbacks
**Consult when:** mapping XBRL concepts onto model line items.
- Revenue: try `RevenueFromContractWithCustomerExcludingAssessedTax` (ASC 606 era) → `Revenues` → `RevenueFromContractWithCustomerIncludingAssessedTax` → `SalesRevenueNet` (pre-ASC 606, deprecated; Apple still has historical facts under it — [companyfacts](https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json)). Banks and insurers use different revenue concepts. Stitch history across tags by period, preferring the newest tag where they overlap.
- Operating income: `OperatingIncomeLoss`. Many filers, and most banks, don't report it. Don't impute it silently.
- Net income: `NetIncomeLoss` is attributable to the parent. `ProfitLoss` includes NCI. Use `NetIncomeLossAttributableToNoncontrollingInterest` to reconcile. EPS and the equity bridge use the parent figure.
- EPS: `EarningsPerShareBasic` and `EarningsPerShareDiluted`, in USD/shares.
- Shares:
  - `dei:EntityCommonStockSharesOutstanding` is the cover-page count as of a date near filing. It is the best "current" basic count, but it can be per class. Sum the class rows, which are separate facts.
  - `WeightedAverageNumberOfDilutedSharesOutstanding` is a period average used for EPS. Never use it as the point-in-time count in an equity bridge.
- D&A: `DepreciationDepletionAndAmortization`, `DepreciationAndAmortization` or `DepreciationAmortizationAndAccretionNet` from the cash-flow statement. Some filers split depreciation and `AmortizationOfIntangibleAssets`.
- Capex: `PaymentsToAcquirePropertyPlantAndEquipment`. Some filers use `PaymentsToAcquireProductiveAssets` or extension tags. Capitalized software may be separate.
- SBC: `ShareBasedCompensation` is the cash-flow add-back. `AllocatedShareBasedCompensationExpense` is the income-statement expense from the footnote. They can differ because of capitalized SBC.
- Debt: `LongTermDebt`, `LongTermDebtNoncurrent`, `LongTermDebtCurrent`, `DebtCurrent`, `ShortTermBorrowings`, `CommercialPaper`, and `OperatingLeaseLiability` / `FinanceLeaseLiability` (ASC 842). Check whether current maturities are inside or outside the total you take, so you don't double-count.
- Extension-tag trap: companies create custom concepts in their own namespace for non-standard items. These are not in `us-gaap` in companyfacts. If a standard tag is missing, the line likely exists under an extension or only as a dimension member. Company-level APIs do not return dimensional (segment) facts, so segment data needs the filing's instance document.
- 2026 GAAP taxonomy: released December 2025, SEC-accepted March 2026, covers ASUs issued before 2025-12-01 — [XBRL International](https://www.xbrl.org/news/sec-accepts-fasbs-2026-taxonomies/), as of 2026-03.

