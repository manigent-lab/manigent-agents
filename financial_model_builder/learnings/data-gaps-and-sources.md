## Shippable reference data
| Data | URL | Licence | Ship? | Notes |
|---|---|---|---|---|
| SEC EDGAR companyfacts / submissions bulk ZIPs and APIs | https://www.sec.gov/search-filings/edgar-application-programming-interfaces | US government public data (no copyright statement; "anyone can access and download") | ship | Must respect 10 req/s and User-Agent when re-fetching; filer-authored text is generally public record |
| US Treasury daily par yield curve CSV | https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve | US government work, public domain | ship | Snapshot dated; 10y 5.24% on 2026-10-09 |
| FASB US GAAP Financial Reporting Taxonomy 2026 | https://xbrl.fasb.org/us-gaap/2026/elts/us-gaap-2026.xsd | © Financial Accounting Foundation; custom "Authorized Uses" notice: royalty-free use, no modification, notice must be retained | do-not-ship | Not an OSI/CC licence; link instead ([terms](https://xbrl.fasb.org/terms/TaxonomiesTermsConditions.html)) |
| Damodaran ERP by month, betas, ratings, CRP | https://pages.stern.nyu.edu/~adamodar/New_Home_Page/data.html | No formal licence; [usage rules](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datahistory.html) say "no strings attached", attribution appreciated | do-not-ship | Informal permission only; underlying data from commercial vendors; link and cite the date |
| FRED series (e.g., DGS10) | https://fred.stlouisfed.org/ | FRED terms; many series third-party copyrighted | do-not-ship | Use Treasury CSV directly for yields instead |

## Gaps
- Current LBO leverage norms (debt/EBITDA by deal size, 2026): no primary source; LCD/PitchBook paywalled.
- FASB ASU list unreadable (403). 2025–2026 ASU dates come from PwC/Deloitte/KPMG. ASU 2026-02 comes from a secondary blog. ASUs after August 2026 are unknown.
- Damodaran synthetic-rating cut-offs and spreads not transcribed; read the live table.
- ASU 2023-09 threshold wording and ASU 2024-03 captions come from secondary summaries.
- The 80% NOL limit and §382 come from general knowledge and were not re-verified.
- Damodaran's 5.29% Oct-1 rate matches Treasury's 2026-09-30 10y; Treasury's 2026-10-01 10y was 5.24%.

## Sources
- [SEC EDGAR application programming interfaces](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [SEC Accessing EDGAR data (fair access)](https://www.sec.gov/os/accessing-edgar-data)
- [Damodaran home page (current ERP)](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm)
- [Damodaran data page / update dates](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/data.html)
- [Damodaran variable definitions](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/variable.htm)
- [Damodaran US industry betas](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html)
- [Damodaran synthetic ratings](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.html)
- [US Treasury daily par yield curve 2026 CSV](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2026/all?type=daily_treasury_yield_curve&field_tdr_date_value=2026&page&_format=csv)
- [IRS Notice 2026-11](https://www.irs.gov/pub/irs-drop/n-26-11.pdf)
- [IRS Instructions for Form 4562 (2025)](https://www.irs.gov/instructions/i4562)
- [IRS Rev. Proc. 2025-28](https://www.irs.gov/pub/irs-drop/rp-25-28.pdf)
- [IRS Instructions for Form 6765](https://www.irs.gov/pub/irs-pdf/i6765.pdf)
- [IRS 163(j) Q&A](https://www.irs.gov/newsroom/questions-and-answers-about-the-limitation-on-the-deduction-for-business-interest-expense)
- [IRS Instructions for Form 1120 (2025)](https://www.irs.gov/pub/irs-pdf/i1120.pdf)
- [PwC Viewpoint: effective dates for public companies](https://viewpoint.pwc.com/dt/us/en/pwc/effective_dates_of_f/public_companies/public_companies_US/standards_effective__US.html)
- [KPMG SEC reporting (ASU 2023-07)](https://kpmg.com/kpmg-us/content/dam/kpmg/pdf/2024/sec-reporting-accounting.pdf)
- [Cherry Bekaert: ASU 2023-09](https://www.cbh.com/insights/articles/asu-2023-09-fasbs-income-tax-rule-for-public-companies/)
- [XBRL International: SEC accepts FASB 2026 taxonomies](https://www.xbrl.org/news/sec-accepts-fasbs-2026-taxonomies/)
- [FASB Taxonomies Authorized Uses](https://xbrl.fasb.org/terms/TaxonomiesTermsConditions.html)
- [Microsoft: circular references / iterative calculation](https://support.microsoft.com/en-us/office/remove-or-allow-a-circular-reference-in-excel-8540bd0f-6e97-4483-bcf7-1b49cd50d123)
- [Microsoft: XIRR](https://support.microsoft.com/en-us/office/xirr-function-de1242ec-6477-445b-b11b-a303ad9adc9d)
