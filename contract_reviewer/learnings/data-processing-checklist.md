# §5 Data-processing checklist: GDPR Art. 28, SCCs, DPF, US state laws

Compiled 2026-10-10 (as-of dates inline). Section numbers §1-§8 refer to the topic files listed in INDEX.md.

**Consult when:** you are reviewing a DPA, a sub-processor clause, or a transfer mechanism.

**GDPR Art. 28(3)** ([EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679); [as-adopted text](https://www.legislation.gov.uk/eur/2016/679/article/28/adopted)). The contract must state the subject-matter, duration, nature and purpose of processing, the data types, the data-subject categories, and the controller's rights and obligations. It must require the processor to meet each of the following:
- [ ] (a) Process only on **documented instructions**, including for transfers. If the law compels otherwise, tell the controller first unless that is prohibited.
- [ ] (b) Personnel are under **confidentiality**.
- [ ] (c) **Art. 32** security.
- [ ] (d) Respect the **Art. 28(2)/(4)** sub-processor conditions.
- [ ] (e) **Assist with data-subject rights** requests.
- [ ] (f) **Assist with Arts. 32–36**: security, breach notification, DPIAs, consultation.
- [ ] (g) **Delete or return** at the controller's choice at the end of services.
- [ ] (h) Provide all compliance information and "allow for and contribute to audits, including inspections".
- [ ] The processor must "immediately inform" the controller of any instruction it believes infringes the law.

**Breach notice.** Art. 28(3)(f) only requires the processor to assist; the 72 hours in Art. 33 is the controller's deadline to the regulator. A processor deadline of 24-72 hours is normal (Bonterms DPA v2: 48h; Common Paper DPA: 72h), so do not flag 48h or 72h as a problem.

**Art. 28(2)/(4).** Sub-processors need **prior specific or general written authorisation**; under general authorisation the controller must be informed of changes and able to **object**; obligations flow down by contract; the initial processor stays **fully liable**. Check notice length, delivery (push vs a page to poll), and the objection remedy (compare §1).

**SCCs, Decision (EU) 2021/914** ([Commission Q&A](https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/new-standard-contractual-clauses-questions-and-answers-overview_en)):
- **Modules:** 1 C2C; 2 C2P; 3 P2P; 4 P2C.
- Modules 2 and 3 incorporate Art. 28.
- Sub-processor Clause 9 offers Option 1 (specific authorisation) or Option 2 (general authorisation with a notice period).
- Docking clause is optional.
- Old SCCs expired **Dec 27, 2022** ([McCann FitzGerald](https://www.mccannfitzgerald.com/knowledge/gdpr/european-commission-adopts-new-sets-of-standard-contractual-clauses)).
- The SCCs **do not fit** importers already subject to the GDPR under Art. 3. A separate set is still in development (as of 2026-10).
- Check that the module matches the actual roles. The UK Addendum and Swiss terms are separate.

**EU-US DPF (as of 2026-10).** Adopted **July 10, 2023** ([Commission](https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/eu-us-data-transfers_en)); General Court dismissed *Latombe* (T-553/23) on **Sept 3, 2025**; appeal **C-703/25 P** pending ([OJ C/2025/6610](https://eur-lex.europa.eu/eli/C/2025/6610/oj/deu/pdf)). Covers only certified importers; keep SCCs as fallback.

**Scope rule.** Apply this checklist only when a DPA or data-processing terms are in front of you; for an excerpt without them, say in one line that the DPA was not reviewed.

**HIPAA.** If the counterparty will create, receive, keep or send PHI for a covered entity, a business associate agreement is required: see hipaa-baa.md.

**CCPA.** [Civ. Code §1798.100(d)](https://cppa.ca.gov/pdf/20260101_ccpa_statute.pdf): agreements with service providers, contractors and third parties must limit use to specified purposes, require same-level protection, give the business reasonable-steps and stop-and-remediate rights, and require notice of inability to comply.

[Regs §7051(a)](https://cppa.ca.gov/regulations/pdf/ccpa_statute_eff_20260101.pdf) (effective **1/1/2026**) adds:
- [ ] No **selling or sharing**.
- [ ] **Specific** business purposes. "The entire contract" is too generic.
- [ ] No use outside those purposes or **outside the direct relationship**, and no combining of data unless permitted.
- [ ] CCPA compliance. Examples given: help with consumer requests, **cybersecurity audits (Art. 9), risk assessments (Art. 10), ADMT (Art. 11)**, and §1798.81.5 security.
- [ ] Business oversight rights, e.g. assessments **at least once every 12 months**.
- [ ] Notice of inability to comply.
- [ ] Stop-and-remediate rights.
- [ ] Consumer-request support.
- [ ] §7051(b): subcontractor flow-down.
- **Consequence:** without a compliant contract the recipient is **not a service provider** (§7050(e)), and the disclosure may be a sale or share. Under §7051(c), a business that never audits weakens its defense.

**Virginia [§59.1-579(B)](https://law.lis.virginia.gov/vacode/title59.1/chapter53/section59.1-579/).** The contract must state instructions, nature/purpose, data types, duration, and rights/obligations, and require: confidentiality; deletion or return at end; compliance information on request; reasonable assessments or an independent assessor's report; written subcontractor flow-down.
