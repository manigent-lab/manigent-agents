## SEC EDGAR APIs: endpoints and access rules
**Consult when:** writing any code that hits data.sec.gov.
- Endpoints ([SEC](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), as of 2026-10-11):
  - `https://data.sec.gov/submissions/CIK##########.json`: filing history and metadata.
  - `https://data.sec.gov/api/xbrl/companyconcept/CIK##########/{taxonomy}/{tag}.json`: one concept for one company, with one array per unit.
  - `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`: every concept for one company.
  - `https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json`: one fact per filer for a calendar period. The pattern is inferred from SEC's example `frames/us-gaap/AccountsPayableCurrent/USD/CY2019Q1I.json`.
- CIK is the 10-digit form with leading zeros, e.g. `str(cik).zfill(10)`. Ticker-to-CIK mapping comes from SEC's company tickers file. Never pass a ticker to these endpoints.
- Frames period codes:
  - `CY####`: annual, with duration 365 days ±30.
  - `CY####Q#`: quarterly, with duration 91 days ±30.
  - `CY####Q#I`: instantaneous, for balance-sheet items. Asking for a balance-sheet item without the `I` returns nothing useful.
- Frames return the "last filed" fact that best fits the calendar period. SEC warns that start and end dates inside one frame can differ across filers, so fiscal years ending in non-December months are approximated.
- No authentication or API key is needed. Updates are near real time: submissions in under 1 second, XBRL in under 1 minute, slower at peak.
- Bulk files `companyfacts.zip` and `submissions.zip` are rebuilt nightly at about 03:00 ET.
- Fair access ([SEC](https://www.sec.gov/os/accessing-edgar-data), as of 2026-10-11):
  - Maximum 10 requests/s.
  - Declare a User-Agent such as "Company Name admin@domain.com".
  - Send `Accept-Encoding: gzip, deflate`.
  - SEC "reserves the right to limit request rates", and non-compliant automated traffic is throttled or blocked.
  - In Python, add a token-bucket throttle and a single session with the headers.

