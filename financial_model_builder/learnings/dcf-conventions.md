## DCF conventions
**Consult when:** discounting, computing terminal value or reconciling FCF definitions.
- **Unlevered FCF** = EBIT × (1 − t) + D&A − capex − ΔNWC. Use cash taxes where they differ materially from book (OBBBA expensing).
- **Discounting:**
  - With mid-year convention, the discount factor for year t is 1/(1+WACC)^(t − 0.5).
  - With a stub period of fraction s, the first-period factor uses s/2 and later periods use s + (t − 1) − 0.5, consistently. Pro-rate stub-year FCF by s.
- **Terminal value:**
  - Gordon TV at the end of year N = FCF_{N+1}/(WACC − g). Discount it with the same exponent as year N's mid-year flow (N − 0.5) to stay consistent with flows arriving mid-year. Discounting at N is the conservative convention. State which one you used.
  - Exit-multiple TV is a point-in-time transaction value at the end of year N, so it is discounted at N even when flows use mid-year.
  - Mixing the two conventions inside one sensitivity table is a common audit finding.
- **Terminal growth:**
  - g ≤ the long-run nominal riskfree rate is Damodaran's ceiling and a common audit test.
  - Check that the reinvestment rate implied by g and terminal ROIC (g/ROIC) is consistent with terminal capex − D&A + ΔNWC.
  - Terminal capex should exceed D&A when g > 0.
- **SBC:** either treat it as a cash expense (don't add it back to FCF) and use current diluted shares, or add it back and fully dilute for future grants. Doing both double-counts. Excluding it from expense and ignoring future dilution overstates value.
- **ASC 842 leases:**
  - Under US GAAP, operating lease cost sits in opex, so EBITDA is post-rent. Under IFRS 16 it is depreciation plus interest.
  - Rule: if lease liabilities are in net debt, EBITDA and FCF must exclude lease cost, and WACC weights must include leases. If not, keep rent in opex and exclude lease liabilities.
  - Comps must use the same treatment, which matters especially when mixing US GAAP and IFRS peers.
- **NOLs:** model the federal NOL as a separate tax asset. Post-2017 NOLs are limited to 80% of taxable income and carried forward indefinitely. Value it as discounted tax savings, or reduce cash taxes in the forecast, but not both. Check for §382 limits after ownership changes.

