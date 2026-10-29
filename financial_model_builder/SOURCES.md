# Sources: financial_model_builder

| File | Source | License | Author | Adapted |
|------|--------|---------|--------|---------|
| role.md | https://github.com/anthropics/financial-services/blob/574ed3624aebd0418c7e96cd101262f30210ab26/plugins/agent-plugins/model-builder/agents/model-builder.md | Apache-2.0 | Anthropic, PBC | persona and stop-and-surface workflow rewritten in our own words; CapIQ/Daloopa pulls replaced by SEC EDGAR; answer-style, conventions, rules, skills and escalation sections added; base-model-errors list copied verbatim from the pool's field-knowledge file (Manigent Contributors, 2026-10-11) |
| role.md | https://github.com/anthropics/financial-services/blob/574ed3624aebd0418c7e96cd101262f30210ab26/plugins/agent-plugins/model-builder/skills/audit-xls/SKILL.md | Apache-2.0 | Anthropic, PBC | "balance first, report before fixing" audit stance paraphrased into the Rules section (Manigent Contributors) |
| skills/model-auditor/SKILL.md | https://github.com/anthropics/financial-services/blob/574ed3624aebd0418c7e96cd101262f30210ab26/plugins/agent-plugins/model-builder/skills/audit-xls/SKILL.md | Apache-2.0 | Anthropic, PBC | checklist trimmed, rewritten around the scripted checker and merged with the pool's linkage and circularity rules; modification notice in the file (Manigent Contributors, 2026-10-11) |
| skills/dcf-validator/SKILL.md | https://github.com/anthropics/financial-services/blob/574ed3624aebd0418c7e96cd101262f30210ab26/plugins/agent-plugins/model-builder/skills/dcf-model/scripts/validate_dcf.py | Apache-2.0 | Anthropic, PBC | check list (g < WACC, WACC band, TV share of EV, formula errors) followed; riskfree ceiling, mid-year/stub and TV-timing checks added; notice in the file. No code copied (Manigent Contributors, 2026-10-11) |
| skills/xlsx-io/SKILL.md | https://github.com/anthropics/financial-services/blob/574ed3624aebd0418c7e96cd101262f30210ab26/plugins/agent-plugins/model-builder/skills/xlsx-author/SKILL.md | Apache-2.0 | Anthropic, PBC | colour code, inputs tab, Checks tab and one-model-per-file conventions paraphrased; output-path contract and Office branches removed; reading and recalculation sections added; notice in the file (Manigent Contributors, 2026-10-11) |
| skills/xlsx-io/SKILL.md | https://github.com/anthropics/financial-services/blob/574ed3624aebd0418c7e96cd101262f30210ab26/plugins/agent-plugins/model-builder/skills/dcf-model/SKILL.md | Apache-2.0 | Anthropic, PBC | formulas-over-hardcodes, row-planning, source-comment and odd-sized centred sensitivity-table rules paraphrased (Manigent Contributors, 2026-10-11) |
| agent.json | original | MIT | Manigent Contributors | written for this pool |
| learnings/ | original | MIT | Manigent Contributors | verbatim split of the pool's financial-model-builder field-knowledge file (compiled 2026-10-11, SHA-256 547a7ba5a88ee4909f5fbbdf54dc255ec46d6a6a9fe40c0b7758c6c51e9b4cd1), one topic page per section; US federal sources (SEC, IRS, Treasury) quoted where marked; Damodaran, PwC, KPMG, Deloitte, Cherry Bekaert, XBRL International and Microsoft pages cited by link, facts restated |
| learnings/INDEX.md | original | MIT | Manigent Contributors | written for this pool |
| learnings/log.md | original | MIT | Manigent Contributors | written for this pool (build entry; later entries by the agent's reflect pass) |
| knowledge/treasury-par-yield-curve-2026.csv | original | MIT | Manigent Contributors | not original data: unmodified US Treasury Daily Par Yield Curve Rates CSV for 2026 (US government work, public domain), fetched 2026-10-11; see Notes |
| knowledge/treasury-par-yield-curve-README.md | original | MIT | Manigent Contributors | written for this pool to describe the CSV |
| skills/edgar-facts/ | original | MIT | Manigent Contributors | written for this pool; stdlib-only helper and synthetic-fixture tests; network pattern follows fda_device_regulatory/skills/openfda-device |
| skills/model-auditor/model_auditor.py | original | MIT | Manigent Contributors | written for this pool (CSV mode stdlib-only; xlsx mode uses openpyxl as a runtime library) |
| skills/model-auditor/test_model_auditor.py | original | MIT | Manigent Contributors | written for this pool; synthetic statements and workbooks |
| skills/dcf-validator/dcf_validator.py | original | MIT | Manigent Contributors | written for this pool; no code from validate_dcf.py |
| skills/dcf-validator/test_dcf_validator.py | original | MIT | Manigent Contributors | written for this pool; synthetic inputs |
| skills/market-inputs/ | original | MIT | Manigent Contributors | written for this pool (2026-10-11); stdlib-only fetcher for the US Treasury par yield CSV and Damodaran's ERPbymonth.xlsx (fetched at runtime, never shipped), synthetic-fixture tests |
| skills/valuation-calc/ | original | MIT | Manigent Contributors | written for this pool; stdlib-only functions and identity-based tests |
| evals/ | original | MIT | Manigent Contributors | results/.gitkeep placeholder only; held-out tasks are not in this folder |

## Notes

- **Persona licence.** anthropics/financial-services is licensed Apache-2.0 by its
  repository-root `LICENSE` (checked at the pinned commit
  `574ed3624aebd0418c7e96cd101262f30210ab26`, repo HEAD on 2026-10-11, committed
  2026-09-21). None of the adapted files (`model-builder.md`, `audit-xls/SKILL.md`,
  `xlsx-author/SKILL.md`, `dcf-model/SKILL.md`, `dcf-model/scripts/validate_dcf.py`)
  carries its own licence header, and no per-plugin licence file exists under
  `plugins/agent-plugins/model-builder/`; the only other licence files in the repo cover
  `plugins/partner-built/spglobal/` and `financial-analysis/skills/skill-creator/`, neither
  used here. The root LICENSE has no copyright line; the card and the plugin manifest
  ("Anthropic FSI") identify the author as Anthropic, PBC. Each adapted file carries a
  modification notice. **agents/NOTICE needs an `anthropics/financial-services
  (Apache-2.0)` block naming these files**; it is not added from this folder.
- **Not adapted:** `3-statement-model`, `lbo-model` and `comps-analysis` were read for
  scope only; no text from them is reproduced. The S&P Capital IQ / LSEG / Daloopa
  partner material is paid and excluded.
- **Python is MIT.** Every `.py` file here was written for this pool (the pool's SPDX rule
  requires MIT under `agents/`). `dcf_validator.py` implements its own checks; nothing
  from `validate_dcf.py` was copied.
- **knowledge/ data provenance.** `treasury-par-yield-curve-2026.csv` is the unmodified
  download of
  `https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2026/all?type=daily_treasury_yield_curve&field_tdr_date_value=2026&page&_format=csv`
  fetched 2026-10-11 (195 rows, 2026-01-02 to 2026-10-09, SHA-256
  `0e7164f6f348497a4541b61ce9b3e76fc00902c988540d08332a7d956350c764`). US government
  work, public domain (17 USC 105). The row is MIT only as a placeholder for the checker;
  the data carry no copyright.
- **Not shipped (per the field-knowledge file's Shippable table):** the FASB US GAAP
  taxonomy (Financial Accounting Foundation "Authorized Uses" terms, not an open
  licence), Damodaran datasets (informal permission, vendor-derived data) and FRED series
  (third-party terms). They are linked and cited by date only. No EDGAR companyfacts
  file is shipped: the skill's tests use a synthetic document, and shipping a real
  filer's facts could overlap with held-out evaluation material.
