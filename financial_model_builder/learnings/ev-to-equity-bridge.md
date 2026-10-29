## Enterprise value to equity value bridge
**Consult when:** converting EV to per-share value or EV comps.
- Equity value = EV − debt (at market or fair value if distressed) − finance and, if consistent, operating lease liabilities − preferred stock − NCI (market value if available) − unfunded pension/OPEB (after tax) + cash and liquid investments + equity-method investments and other non-operating assets + NOL value if not already in FCF.
- Consistency rule: every item you subtract must have its income excluded from the FCF or EBITDA you valued. Equity-method income is not in EBITDA, so the investment is added. NCI's share of EBITDA is in consolidated EBITDA, so NCI is subtracted.
- **Dilution:**
  - Options and warrants use the treasury stock method: added shares = in-the-money options − (proceeds/price).
  - RSUs and PSUs are added in full; there are no proceeds. Unvested awards are commonly included when SBC is treated as non-cash.
  - Convertibles use if-converted. If in the money, add the conversion shares and remove the debt from the bridge, but never both keep the debt and add the shares. ASU 2020-06 requires if-converted for diluted EPS.
- **Circularity:** in a DCF, the TSM share count depends on the implied price, which depends on the share count. Solve by iteration or a goal-seek / closed-form loop. Using the current market price instead is acceptable only if disclosed. Seed the iteration with the basic share count.

