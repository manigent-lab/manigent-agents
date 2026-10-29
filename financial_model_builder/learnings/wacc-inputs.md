## WACC inputs
**Consult when:** building or auditing a discount rate.
- **Riskfree rate:**
  - Match currency and duration to the cash flows.
  - The 10y Treasury is the usual base. Damodaran uses the 10y T-bond in his ERP series.
  - Using the 20y with an ERP computed against the 10y is an inconsistency. ERP and riskfree must come from the same series.
  - Record the observation date. Fetch it for the valuation date with `market-inputs treasury --as-of`.
- **ERP:**
  - Damodaran's monthly implied ERP is in [ERPbymonth.xlsx](https://pages.stern.nyu.edu/~adamodar/pc/implprem/ERPbymonth.xlsx), annual history in [histimpl.xls](https://pages.stern.nyu.edu/~adamodar/pc/datasets/histimpl.xls), and a daily file for March 2026 is also posted.
  - Fetch the month on or before the valuation date with `market-inputs erp --as-of --variant`, and name the variant. His headline is "T12m with sustainable payout"; the gap to the T12m cash-yield figure varies by month (5 bp to 50 bp in 2026), so fetch the variant you name.
  - Point in time: a valuation dated inside a month uses that month's figure, not a later update.
  - If you use his "adjusted" riskfree rate (Treasury minus US default spread), add the same spread back to the ERP.
- **Beta** ([variable definitions](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/variable.htm), [Betas.html](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html), as of Jan 2026):
  - Damodaran's US industry betas come from regressions of weekly returns, and his datasets are January 2026.
  - Unlevered beta = levered beta / (1 + (1 − t) × D/E), using market D/E.
  - Cash-corrected unlevered beta = unlevered beta / (1 − cash/firm value).
  - Relever with the target's own market D/E and marginal tax rate: βL = βU × (1 + (1 − t) × D/E).
  - Traps: book D/E; mismatched tax rates between unlevering and relevering; leases in the target's D/E but not the comps'.
- **Cost of debt:**
  - Pre-tax Kd = riskfree + default spread. Take the spread from an actual rating or Damodaran's synthetic rating table, which maps interest coverage to a rating and spread ("as of January 2026"), with separate tables for large non-financial firms and financial firms ([ratings.html](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.html)).
  - After-tax Kd uses the marginal rate, not the effective rate. Interest that §163(j) cannot deduct gets no shield.
  - Yield to maturity on traded bonds is better than the coupon.
- **Weights:** market values of equity and debt. Include lease liabilities in debt only if lease cost is removed from operating expense (see the DCF section).
- **Country risk:** add the CRP to the ERP, scaled by the company's revenue exposure or a lambda, not by domicile alone. Damodaran's CRP table was updated 2026-07-01.

