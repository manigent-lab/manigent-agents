# Learnings: contract_reviewer

Each topic page has a one-line "consult when" pointer; under it, the facts a generalist most often gets wrong (recent changes, numbers, codes, effective dates) that I should answer straight from memory. Open the page before relying on one in a live review; flag anything resting on [gaps-and-sources.md](gaps-and-sources.md).

- [§4 Non-competes](non-competes.md) — any post-relationship restraint, or a clause making a worker repay/forfeit on leaving (table: knowledge/noncompete-enforceability-2026.tsv)
  - **FTC non-compete rule is GONE**: vacated *Ryan v. FTC*, FTC dropped appeals Sept 5 2025, 16 CFR part 910 removed eff. **Feb 12 2026** (91 FR 6507). Not "on hold", not "enjoined".
  - CA stay-or-pay AB 692 (§16608, Lab. §926): repayment/quit-fee/sign-on-clawback terms from **Jan 1 2026** are void; damages greater of actual or **$5,000/worker** + fees.
  - FL CHOICE Act §§542.41-.45 (from **July 1 2025**): pay >2x county mean wage → non-compete up to 4 yrs enforceable, 7-day review + written right-to-counsel, court **must** grant prelim injunction; §542.335's 2-yr presumption applies only outside the Act.
  - MN §181.988: void incl. independent contractors (July 1 2023). CA §16600.5: void regardless of where/when signed. TN HB 1034 (eff. July 1 2026, <$70k): secondary source only — check enrolled act.
  - TX SB 1318 (§15.50, from **Sept 1 2025**): physician non-competes ≤1 yr after the relationship, ≤5-mi radius from the primary practice location, buyout ≤ annual salary+wages, void on discharge w/o good cause; §15.501 = dentists/nurses/PAs.
  - VA §40.1-28.7:8: since **July 1 2025** every FLSA non-exempt employee is "low-wage" → no non-compete whatever they earn; from **July 1 2026** none vs an employee discharged without cause unless severance was disclosed at signing.
  - WA ESHB 1155: from **June 30 2027** all non-competes void regardless of signing; worker notice due Oct 1 2027; non-solicits ≤18 mo; $5k min. Until then 2026 thresholds **$126,858.83** employees / **$317,147.09** contractors.
  - WY W.S. 1-23-108: non-competes for skilled/unskilled labor **void**, contracts on/after **July 1 2025** (exc. sale-of-business, trade secrets, execs/managers + their professional staff, training-cost repayment on the statutory sliding scale).
- [§1 Standard-position playbook](standard-position-playbook.md) — market baseline + fallback/walk-away for a clause; carries the "not an issue by default" list (table: knowledge/standard-positions-cp-bonterms.tsv)
  - Common Paper CSA **v3.0** (2026-09-30): no "undefined variable = none" rule (2.1 §13.1), no Increased/Unlimited Claims in the standard text (set on the Cover Page), gross negligence / willful misconduct / fraud uncapped (§8.4), §1.6 Machine Learning deleted. Cite the version the cover page names — fetch it with the `cp-standard` skill.
  - Bonterms Enhanced Cap = **3x** the 12-mo General Cap; DPA v2 incident notice **48h** (§5.2(b)(i)/§1.28), new sub-processor **≥30 days** (§4.3). Common Paper DPA: **72h** / **10 business days**.
  - Bonterms NDA §4 already limits every exclusion (independent development included) to info the recipient **"can document"**; CP has no documentation wording — neither is a deviation. Bonterms §8 **lets a recipient develop similar products** absent breach — don't flag a missing no-competing-products clause.
  - DTSA (18 U.S.C. §1833): individual confidentiality/trade-secret agreements need the whistleblower-immunity notice or the employer loses exemplary damages + fees vs that person.
- [§2 Limitation of liability and indemnity](liability-and-indemnity.md) — caps, super-caps, uncapped carve-outs, indemnity scope/procedure
  - Caps = 12-mo fees "paid **or payable**"; CP General Cap 1x is most common; "paid" alone is near-zero early in a deal; confirm the other side's IP indemnity is uncapped.
- [§3 IP: assignment, licences, feedback, residuals](ip-assignment-licences-residuals.md) — a contract allocating work-product ownership or rights in info/feedback
  - Neither CP nor Bonterms NDAs have a **residuals** (unaided-memory) clause; it is a deviation that can cancel the rest of the NDA's protection. Main discloser of technical/commercially sensitive info → position is deletion (walk-away); narrowing is a fallback, never the opening position.
- [§5 Data-processing checklist](data-processing-checklist.md) — a DPA, sub-processor clause, or transfer mechanism (GDPR Art. 28, SCCs, EU-US DPF, CCPA §7051 eff. 1/1/2026, VA §59.1-579)
  - Processor incident notice 24-72h is normal (Bonterms 48h, CP 72h); GDPR's 72h runs controller→regulator, so don't flag 48/72h.
- [§6 Auto-renewal statutes](auto-renewal-statutes.md) — any auto-renewing contract (table: knowledge/auto-renewal-statutes.tsv)
  - NY GOL §5-903 covers **B2B** service/maintenance/repair; renewal unenforceable unless written notice personally/certified mail **15-30 days** before the deadline — email alone not listed.
  - CA ARL AB 2863 (from **July 1 2025**): price-change notice **7-30 days** before; express affirmative consent; keep records 3 yrs. No federal click-to-cancel rule (16 CFR 425 restored pre-2024 text Feb 12 2026).
- [§7 Assignment, change of control, termination, law/venue](assignment-termination-law-venue.md) — transferability, exit rights, or forum boilerplate
- [§8 Review procedure & escalation](review-procedure-and-escalation.md) — starting a full review, or deciding whether a lawyer is needed
- [HIPAA BAAs](hipaa-baa.md) — a vendor that will create/receive/keep/send PHI for a covered entity
  - BA must report a breach **without unreasonable delay, ≤60 calendar days** (164.410); the 2025 Security Rule 24-hour contingency-plan notice is still only **proposed**.
- [EU Data Act: cloud switching](eu-data-act-cloud-switching.md) — a cloud/SaaS/PaaS/IaaS contract with an EU customer
  - From **Sept 12 2025**: switch on ≤**2 months** notice, 30-day transition, ≥30 days to retrieve; switching charges at cost until **Jan 12 2027**, banned after.
- [Gaps and sources](gaps-and-sources.md) — an answer turning on an unverified point, or the primary-source link / as-of date behind a fact
