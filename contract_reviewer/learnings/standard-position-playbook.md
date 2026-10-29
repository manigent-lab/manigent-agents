# §1 Standard-position playbook: NDA, cloud/SaaS MSA, order form, DPA

Compiled 2026-10-10 (as-of dates inline). Section numbers §1-§8 refer to the topic files listed in INDEX.md.

_Attribution: paraphrases and cites the Common Paper standard agreements (commonpaper.com, CC BY 4.0) and the Bonterms standard agreements (bonterms.com, CC BY 4.0); pinned snapshots are listed in gaps-and-sources.md. Changes: summarized, compared and reorganized by Manigent Contributors._

**Consult when:** you need the market-standard baseline for a clause plus fallback and walk-away positions.

**Baselines (as of 2026-10).**
- Common Paper: [Mutual NDA v1.0](https://commonpaper.com/standards/mutual-nda/1.0), [Cloud Service Agreement (CSA) v2.1](https://commonpaper.com/standards/cloud-service-agreement/2.1) and [v3.0](https://commonpaper.com/standards/cloud-service-agreement/3.0), [DPA v1.1](https://commonpaper.com/standards/data-processing-agreement/). CSA section numbers below are v2.1 unless marked; fetch the version the cover page names with the `cp-standard` skill before citing one.
- Bonterms: [Mutual NDA v1](https://bonterms.com/standard/bonterms-mutual-nda-v1), [Cloud Terms v1](https://bonterms.com/standard/bonterms-cloud-terms-v1), [DPA v2](https://bonterms.com/standard/dpa-v2-attachment-version), [PSA v1.2](https://bonterms.com/standard/professional-services-agreement-v1.2).

In both families, the business variables (term, cap, covered claims, governing law) live on a **Cover Page / Key Terms** that overrides the standard terms, so read it first. Under CP CSA **v2.1** §13.1, an undefined variable means "none / not applicable". Deleting the General Cap Amount therefore means **no cap**, not $0 ([CP cover-page guide](https://commonpaper.com/standards/cloud-service-agreement/)). **v3.0 drops that rule.** It keeps only a narrower one: with no Covered Claims defined, there is no indemnity (§9.1(c)). So under 3.0 a struck cap leaves §8.1 pointing at an undefined General Cap Amount. Flag it as unresolved, and don't read it as "none".

**Mutual NDA (CP and Bonterms agree unless noted).**
- **Confidential Information.** Marked, or reasonably understood as confidential, disclosed for the Purpose, plus the existence of talks (CP §1; Bonterms §2). Fallback: marking plus written confirmation of oral disclosures. Walk-away: captures recipient's own pre-existing material.
- **Exclusions.** Public through no fault of recipient; known before; received from a third party without restriction; independently developed (Bonterms adds that the recipient must *document* it; CP does not, so a plain independent-development exclusion is standard). Walk-away: a carve-out deleted, or one keyed to memory (residuals, §3).
- **Use and sharing.** Purpose only; need-to-know representatives bound by equal terms, recipient liable for them; own-care standard, never below reasonable care.
- **Compelled disclosure.** As legally required, with advance notice where lawful and cooperation at discloser's cost (CP §4; Bonterms §5(b)). Walk-away: no notice duty.
- **Return/destroy.** On expiry or request; certify if asked; backup/retention copies allowed but stay covered. Walk-away: no backup carve-out.
- **Term.** NDA term and confidentiality period are cover-page variables with no numeric default; CP allows termination on notice, obligations survive. Fallback: fixed tail, trade secrets protected while secret.
- **No licence, as-is.** Bonterms §8 goes the other way from what disclosers expect: it expressly lets the recipient build competing products if it does not breach the NDA. So a missing "no competing products" clause is standard, not a gap.
- **Assignment.** Consent required, except on a merger, acquisition or sale of substantially all assets or voting securities. A non-permitted assignment is void.

**DTSA notice (US federal law).** An agreement with an employee, contractor or consultant that governs trade secrets or confidential information must carry the whistleblower-immunity notice, or a cross-reference to a policy containing it. This applies to agreements entered into or updated after **May 11, 2016**. Without it, the employer cannot recover exemplary damages or attorney fees against that individual ([18 U.S.C. §1833(b)(3)](https://www.law.cornell.edu/uscode/text/18/1833)).

**SaaS MSA and order form: CP CSA 2.1 vs Bonterms Cloud Terms v1.** (CSA 3.0 changes are marked "3.0:" in the cell.)
| Clause | Common Paper | Bonterms |
|---|---|---|
| Payment | Set on the cover page; "30 days from receipt" is the most common choice (~62%, per CP). Disputes must be raised before the due date, then a 15-day resolution (§4.6; 3.0: §4.4, and 3.0 drops the separate invoicing and automatic-payment clauses). | Net 30 from invoice date. Late charge 1.5%/month or the legal maximum, whichever is lower. 15-day dispute discussion (§12). |
| Suspension | Undisputed balance more than 30 days overdue, a restriction breach, or harmful use (§2.2). | 30+ days overdue, usage-rule breach, or material harm (§13). |
| Renewal | Auto-renews unless notice is given by the Non-Renewal Notice Date. 30 days is chosen in ~84% of auto-renewing CSAs. | 12-month initial term. Auto-renews unless notice is given ≥30 days before term end. No price-increase mechanism in the standard text (§14.1). |
| Termination for cause | 30-day cure. Insolvency proceedings lasting 60+ days. Force majeure lasting 30+ consecutive days allows termination with a prorated refund (§5.3–5.4). | 30-day cure. Insolvency proceeding not dismissed within 60 days (§14.3). |
| Warranty | No material reduction in functionality. Customer gives notice within 45 days; Provider has 45 days to fix, failing which Customer may terminate with a prorated refund (§6.3–6.4). | Performs materially per the Documentation. 30-day claim period and 30-day fix period, then termination with a refund (§8). |
| SLA | None in the standard terms; support per the Order Form. | Cover-page SLA. If none, commercially reasonable efforts toward 99.9% monthly availability. No material mid-term reduction (§7.2, §22.7). |
| Exit data | Delete within 60 days of request (§5.5). | Export during the term. Delete within 60 days of request (§14.4). |
| Usage data / AI | Aggregated and de-identified only. Model training only on aggregated, de-identified data (§1.4, §1.6). 3.0: §1.6 Machine Learning is deleted, so no standard training right; §1.4 usage-data use stays. | Disclosure only if de-identified and aggregated (§5.4). |

Customer fallbacks (reviewer judgment, not sourced): renewal price cap, post-termination export window, termination for chronic SLA failure.

**DPA numbers** (Bonterms DPA v2.0 section numbers re-read on bonterms.com 2026-10-11).
| Term | CP DPA v1.1 | Bonterms DPA v2 |
|---|---|---|
| New sub-processor notice | 10 business days. 30 days to object; silence counts as acceptance; good-faith resolution (§2.6). | At least 30 days before the new sub-processor touches data (§4.3). 30 days to object on reasonable grounds; if unresolved, terminate the affected part with a refund of prepaid unused fees, as the sole remedy (§4.4). |
| Incident notice | ≤72 hours (§4). | ≤48 hours: the "Specified Notice Period" (§5.2(b)(i), defined in §1.28). |
| Audit | Information, third-party report summary, annual questionnaire. Records kept 3 years after the DPA ends (§5). | Reports first (§9.2). On-site audit only if reports are insufficient, a regulator requires it, or after an incident. At most once a year (§9.3(c)(iv)), by an independent auditor, at Customer's cost. |
| Liability | Follows the main agreement's cap unless the cover page sets a separate DPA cap (§8). | Follows the main agreement (§2.6). |
| SCCs | Module 2 or 3. Clause 9 Option 2. No docking clause. Clause 17 Option 1 (§3.2). | Module 2 or 3. Option 2 for sub-processors. Clause 17 Option 1. |

**Not an issue by default** (both standards accept these; do not list them as issues unless the user's own playbook says otherwise or the deal facts make them matter):
- independent-development exclusion without a documentation requirement;
- no clause barring the recipient from building competing products, where an independent-development exclusion exists;
- backup / archival copies kept after return-or-destroy, if they stay confidential;
- incident notice to the customer anywhere from 24 to 72 hours, or "without undue delay" with a 72-hour outer limit (GDPR Art. 33's 72 hours runs from the controller to the regulator, so it is not a processor norm either way);
- sub-processor changes notified by list update plus email, with termination of the affected service as the objection remedy;
- a 12-month "paid or payable" cap, a 2x-3x super-cap for data claims, no data-breach indemnity;
- a 30-day non-renewal notice; an M&A assignment exception that runs to both parties;
- an integration clause that names only the agreement and its order forms.
Table form, with the source of each position: `knowledge/standard-positions-cp-bonterms.tsv`.
