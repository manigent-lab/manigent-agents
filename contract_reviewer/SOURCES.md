# Sources - contract_reviewer

| File | Source | License | Author | Adapted |
|------|--------|---------|--------|---------|
| role.md | https://github.com/anthropics/knowledge-work-plugins/blob/95bdacc803aa5cfdb10f35e5b9fb2d4b11100133/legal/skills/review-contract/SKILL.md | Apache-2.0 | Anthropic, PBC | review procedure merged into one persona; CLM/connector steps and local playbook lookup removed; pool playbook, statutory overlays and escalation guardrails added (Manigent Contributors, 2026-10-10); direct-answer rule, base-model-errors list and scoped memo format added, escalation narrowed (2026-10-11) |
| role.md | https://github.com/anthropics/knowledge-work-plugins/blob/95bdacc803aa5cfdb10f35e5b9fb2d4b11100133/legal/skills/triage-nda/SKILL.md | Apache-2.0 | Anthropic, PBC | GREEN / YELLOW / RED NDA triage folded into the persona; trimmed (Manigent Contributors) |
| role.md | https://github.com/anthropics/knowledge-work-plugins/blob/95bdacc803aa5cfdb10f35e5b9fb2d4b11100133/legal/skills/legal-risk-assessment/SKILL.md | Apache-2.0 | Anthropic, PBC | severity-by-likelihood framing folded into the persona; trimmed (Manigent Contributors) |
| agent.json | original | MIT | Manigent Contributors | written for this pool |
| learnings/standard-position-playbook.md | https://web.archive.org/web/20250823132938/https://commonpaper.com/standards/cloud-service-agreement/2.1/ | CC-BY-4.0 | Common Paper, Inc. | positions paraphrased, compared and reorganized into standard / fallback / walk-away by Manigent Contributors; also draws on the Common Paper Mutual NDA v1.0 and DPA snapshots listed in gaps-and-sources.md |
| learnings/standard-position-playbook.md | https://web.archive.org/web/20260417122340/https://bonterms.com/standard/bonterms-cloud-terms-v1 | CC-BY-4.0 | Bonterms, Inc. | positions paraphrased and compared with Common Paper by Manigent Contributors; also draws on the Bonterms Mutual NDA v1 and PSA v1.2 snapshots |
| learnings/liability-and-indemnity.md | https://web.archive.org/web/20250823132938/https://commonpaper.com/standards/cloud-service-agreement/2.1/ | CC-BY-4.0 | Common Paper, Inc. | cap, carve-out and indemnity terms paraphrased and summarized by Manigent Contributors |
| learnings/standard-position-playbook.md | https://github.com/CommonPaper/CSA/blob/3efceb01e3c8bfb7b302a5f34975aa2b084026a3/CSA.md | CC-BY-4.0 | Common Paper, Inc. | CSA v3.0 differences (§13.1 default removed, §4 renumbering, §1.6 deleted) paraphrased by Manigent Contributors (2026-10-11) |
| learnings/liability-and-indemnity.md | https://github.com/CommonPaper/CSA/blob/3efceb01e3c8bfb7b302a5f34975aa2b084026a3/CSA.md | CC-BY-4.0 | Common Paper, Inc. | CSA v3.0 cap, exception and indemnity changes (§8.1, §8.4, §9.1(c)) paraphrased by Manigent Contributors (2026-10-11) |
| learnings/liability-and-indemnity.md | https://web.archive.org/web/20260417122340/https://bonterms.com/standard/bonterms-cloud-terms-v1 | CC-BY-4.0 | Bonterms, Inc. | cap, carve-out and indemnity terms paraphrased and compared by Manigent Contributors |
| learnings/ip-assignment-licences-residuals.md | https://web.archive.org/web/20240705150231/https://commonpaper.com/standards/mutual-nda/1.0 | CC-BY-4.0 | Common Paper, Inc. | NDA and IP terms paraphrased by Manigent Contributors |
| learnings/ip-assignment-licences-residuals.md | https://web.archive.org/web/20260617102117/https://bonterms.com/standard/professional-services-agreement-v1.2 | CC-BY-4.0 | Bonterms, Inc. | services IP terms paraphrased by Manigent Contributors |
| learnings/assignment-termination-law-venue.md | https://web.archive.org/web/20250823132938/https://commonpaper.com/standards/cloud-service-agreement/2.1/ | CC-BY-4.0 | Common Paper, Inc. | assignment, termination and venue terms paraphrased by Manigent Contributors |
| learnings/assignment-termination-law-venue.md | https://web.archive.org/web/20260617102117/https://bonterms.com/standard/professional-services-agreement-v1.2 | CC-BY-4.0 | Bonterms, Inc. | termination-for-convenience and assignment terms paraphrased by Manigent Contributors |
| learnings/ | original | MIT | Manigent Contributors | split from the pool's contract_reviewer field-knowledge file (2026-10-10); statutes and regulations (NY GOL, Cal. B&P, Minn. Stat., GDPR, 91 FR 6507) cited and briefly quoted where marked |
| learnings/hipaa-baa.md | original | MIT | Manigent Contributors | written for this pool from 45 CFR Part 164 (HIPAA Privacy, Security and Breach Notification Rules: §§164.314(a), 164.410, 164.502(e), 164.504(e)), https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164 (US federal regulation, no copyright); paraphrased with short quotes |
| learnings/eu-data-act-cloud-switching.md | original | MIT | Manigent Contributors | written for this pool from Regulation (EU) 2023/2854 (Data Act), Articles 13, 23-31 and 50, https://eur-lex.europa.eu/eli/reg/2023/2854/oj (EU legislation, reuse permitted under Commission Decision 2011/833/EU); paraphrased with short quotes |
| learnings/log.md | original | MIT | Manigent Contributors | written by the agent's reflect pass over its own field notes |
| knowledge/standard-positions-cp-bonterms.tsv | https://web.archive.org/web/20250823132938/https://commonpaper.com/standards/cloud-service-agreement/2.1/ | CC-BY-4.0 | Common Paper, Inc. | Common Paper CSA, NDA and DPA positions paraphrased into a comparison table with a "not an issue by default" column by Manigent Contributors (2026-10-11); other pinned CP snapshots listed in learnings/gaps-and-sources.md |
| knowledge/standard-positions-cp-bonterms.tsv | https://web.archive.org/web/20260417122340/https://bonterms.com/standard/bonterms-cloud-terms-v1 | CC-BY-4.0 | Bonterms, Inc. | Bonterms Cloud Terms, Mutual NDA and DPA v2.0 positions paraphrased and compared by Manigent Contributors (2026-10-11); DPA v2.0 has no immutable snapshot (see Notes) |
| knowledge/standard-positions-cp-bonterms.tsv | https://github.com/CommonPaper/CSA/blob/3efceb01e3c8bfb7b302a5f34975aa2b084026a3/CSA.md | CC-BY-4.0 | Common Paper, Inc. | CSA v3.0 differences added to the super-cap, uncapped-claims, renewal, exit-data and assignment rows by Manigent Contributors (2026-10-11) |
| knowledge/common-paper-csa/CSA-2.1.md | https://github.com/CommonPaper/CSA/blob/aaaa2826a0c853371bcda13a612e9874dd474f1e/CSA.md | CC-BY-4.0 | Common Paper, Inc. | none: verbatim copy of the Standard Terms at tag 2.1, kept as the cp-standard skill's offline source |
| knowledge/common-paper-csa/CSA-3.0.md | https://github.com/CommonPaper/CSA/blob/3efceb01e3c8bfb7b302a5f34975aa2b084026a3/CSA.md | CC-BY-4.0 | Common Paper, Inc. | none: verbatim copy of the Standard Terms Version 3.0 on main (2026-09-30), kept as the cp-standard skill's offline source |
| knowledge/noncompete-enforceability-2026.tsv | original | MIT | Manigent Contributors | compiled 2026-10-11 from public law (state statutes, session laws, Federal Register); facts restated, not copied; per-row source URL and verified flag in the file; provenance note below |
| knowledge/auto-renewal-statutes.tsv | original | MIT | Manigent Contributors | compiled 2026-10-11 from public law (state statutes, Federal Register); facts restated, not copied; per-row source URL and verified flag in the file |
| skills/ | original | MIT | Manigent Contributors | clause-extractor and docx-redline skills and stdlib helpers written for this pool; plain-text redline mode and missing-clause check added 2026-10-11; cp-standard skill (fetches the Common Paper CSA at runtime, section index, version detection and diff) added 2026-10-11 |
| evals/ | original | MIT | Manigent Contributors | held-out tasks, contracts written fresh with planted issues, checkers, checker tests and rubric written for this pool |

## Notes

- **Persona license.** `legal/LICENSE` in anthropics/knowledge-work-plugins at
  the pinned commit is Apache-2.0 (Copyright Anthropic, PBC); it governs the
  three adapted skills. `role.md` carries a modification notice at the top, and
  the repository is named in `agents/NOTICE`.
- **CC BY 4.0 standards.** Common Paper and Bonterms publish their standard
  agreements under CC BY 4.0. The four learnings files above paraphrase them
  and carry an attribution line at the top. All pinned snapshots are listed in
  `learnings/gaps-and-sources.md`. The Bonterms DPA terms are paraphrased
  from **v2.0** (Attachment Version) on bonterms.com, which has no archived
  snapshot; the GitHub commit `68edf622cc850488492d74df62764ee943ef444a` holds
  only v1.0 and is listed for reference, not as the source of the v2.0 section
  numbers.
- **Common Paper CSA copies.** `knowledge/common-paper-csa/` holds the CSA
  Standard Terms verbatim at tag `2.1` and at `main` commit `3efceb0` (Version 3.0, not
  yet tagged), unmodified, under CC BY 4.0 with attribution to Common Paper, Inc. The
  `cp-standard` skill fetches the same files live from GitHub and falls back to these
  copies when the web is off. Version 3.0's text is untagged, so a later commit to `main`
  could change it; the skill reports the ref it read.
- **Fetch caveats.** The California statutes were checked against FindLaw's
  copy (leginfo blocked automated fetching) and Decision (EU) 2021/914 via the
  Commission's Q&A (EUR-Lex blocked). Statute text is public law, cited not
  copied.
- **knowledge/ provenance (statute tables).** Each row of the two statute tables
  restates a US state statute, session law or Federal Register notice (public
  law; no copyright in the text of the law) in Manigent Contributors' own words,
  with the URL read and a `verified` column (primary = the law itself was read on
  2026-10-11; secondary = only a named law-firm summary was read). No law-firm
  text is copied.
- No AMA, AICPA, ISO or commercial-guide text is included.
