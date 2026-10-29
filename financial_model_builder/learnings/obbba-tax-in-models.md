## 2025 US tax law (OBBBA, P.L. 119-21) in models
**Consult when:** forecasting cash taxes, deferred taxes, interest deductibility or capex timing for US entities.
- IRS materials also call P.L. 119-21 the "Working Families Tax Cuts" — [IRS](https://www.irs.gov/newsroom/understanding-the-working-families-tax-cuts-business-tax-provisions-youtube-video-text-script).
- Federal corporate rate is 21% (unchanged) — [Form 1120 instructions](https://www.irs.gov/pub/irs-pdf/i1120.pdf), 2025.
- **Bonus depreciation** ([Notice 2026-11](https://www.irs.gov/pub/irs-drop/n-26-11.pdf); [Form 4562 instructions](https://www.irs.gov/instructions/i4562)):
  - 100% applies to qualified property acquired after 2025-01-19, permanently.
  - An election to take 40% instead (60% for long-production property) exists for the first tax year ending after 2025-01-19.
  - Property acquired before 2025-01-20 stays at 40% and must be placed in service before 2026-01-01.
  - New §168(n) gives a temporary 100% allowance for qualified production property placed in service after 2025-07-04 (Notice 2026-16).
  - §179 for 2025: limit $2.5M, phase-out starting at $4M.
  - Modelling rule: for qualifying US capex, tax depreciation ≈ capex in year 1. This creates a deferred tax liability. The cash tax rate falls below the book rate while capex grows, and it converges when capex flattens. Keep book D&A on the useful-life schedule.
- **R&E** ([Rev. Proc. 2025-28](https://www.irs.gov/pub/irs-drop/rp-25-28.pdf)):
  - §174A allows immediate deduction of domestic R&E paid or incurred in tax years beginning after 2024. Electing to capitalize and amortize over at least 60 months is optional.
  - Software development is treated as R&E.
  - Foreign R&E keeps 15-year amortization.
  - The transition election for 2022–2024 unamortized domestic balances: deduct them all in the first post-2024 year, or split them over 2 years. Many tech filers show a large one-off cash-tax benefit in 2025–2026. Don't extrapolate it.
  - Under the §280C(c) interaction, the deduction is reduced by the R&D credit unless the reduced-credit election is made.
- **§163(j)** ([IRS Q&A](https://www.irs.gov/newsroom/questions-and-answers-about-the-limitation-on-the-deduction-for-business-interest-expense)):
  - The limit is business interest income + 30% × ATI + floor plan interest.
  - ATI adds back D&A again for tax years beginning after 2024.
  - CFC inclusions are excluded from ATI for tax years beginning after 2025.
  - The small-business exemption threshold is $31M for 2025 and $32M for 2026.
  - LBO rule: test deductible interest against 30% of tax EBITDA each year and carry disallowed interest forward. Under OBBBA this binds much less often than under the 2022–2024 EBIT basis.

