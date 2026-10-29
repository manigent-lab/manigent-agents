# §2 Limitation of liability and indemnity

Compiled 2026-10-10 (as-of dates inline). Section numbers §1-§8 refer to the topic files listed in INDEX.md.

_Attribution: paraphrases and cites the Common Paper standard agreements (commonpaper.com, CC BY 4.0) and the Bonterms standard agreements (bonterms.com, CC BY 4.0); pinned snapshots are listed in gaps-and-sources.md. Changes: summarized, compared and reorganized by Manigent Contributors._

**Consult when:** you are assessing caps, super-caps, uncapped carve-outs, or indemnity scope and procedure.

**Caps.** Both standards measure the cap as **fees paid or payable in the 12 months before the claim or first incident**.
- **CP:** the General Cap defaults to a multiple of those 12-month fees, and **1x** is the most common choice. Fixed-dollar and "greater of" options also exist. Increased Claims (pre-selected as privacy/security and confidentiality breaches) carry an Increased Cap that must not be 1x. Only ~13% of CSAs use Increased Claims and ~1% use Unlimited Claims ([CP guide](https://commonpaper.com/standards/cloud-service-agreement/)). That is CSA **v2.1** (§8.1(b), §8.4).
- **CP CSA v3.0** ([3.0](https://commonpaper.com/standards/cloud-service-agreement/3.0)) drops the Increased and Unlimited Claims terms from the standard text:
  - §8.1 is one General Cap "except as provided in the Cover Page", so any super-cap or uncapped claim must be written on the Cover Page;
  - §8.4 now leaves liability for **gross negligence, willful misconduct or fraud** unlimited, alongside what law won't let a contract limit;
  - §8.2 keeps confidentiality breach outside the indirect-damages waiver.
- **Bonterms:** General Cap = 12-month fees. Enhanced Cap = **3x the General Cap**, for Provider's security breach and either party's DPA breach ([Cloud Terms §16](https://bonterms.com/standard/bonterms-cloud-terms-v1)).

**Uncapped claims.**
- **Bonterms:** indemnity obligations; infringement or misappropriation of the other party's IP; confidentiality breach *except* breaches involving Customer Data (those go to the Enhanced Cap); and liability that cannot be limited by law.
- **CP v2.1:** indemnity is pre-selected as an Unlimited Claim. Confidentiality breach is outside the consequential-damages waiver (§8.4). **v3.0:** no standard uncapped indemnity, since uncapping must be set on the Cover Page. Gross negligence, willful misconduct and fraud are uncapped (§8.4). With no Covered Claims defined, there is no indemnity at all (§9.1(c)).
- **Bonterms PSA (services):** also uncaps provider-caused personal injury or property damage from negligence or willful misconduct ([PSA §12](https://bonterms.com/standard/professional-services-agreement-v1.2)).

**Waiver.** Both forms waive lost profits and consequential-type damages (Bonterms adds loss of use and business interruption). Check whether it swallows data-restoration costs or regulatory fines.

**Indemnity defaults.**
- **Provider:** third-party claims that the service, used as authorized, infringes or misappropriates IP.
- **Customer:**
  - CP: Customer Content infringement and breach of the use restrictions.
  - Bonterms: usage-rule breaches and high-risk / sensitive-data misuse.
- **Standard exclusions:** modification, unauthorized use, combinations with non-provider items, and outdated versions when a fix was offered.
- **Mitigation ladder:** procure rights, then modify, then terminate with a refund.
- **Exclusive remedy:** the indemnity is the exclusive remedy for IP claims.
- **Data-breach indemnity is not a default in either standard.** It is handled by the super-cap, so adding one is a negotiated extra.

**Procedure.** Prompt notice (Bonterms: late notice matters only to the extent of prejudice); indemnitor controls the defense; indemnitee may join with its own counsel at its own cost; no settlement admitting fault or binding the indemnitee without consent; cooperation at the indemnitor's cost.

**Review rules.**
1. Map every claim type into one of four buckets for *each* party: general cap, super-cap, uncapped, or waived. Then compare the two sides for symmetry.
2. Check the look-back basis. "Paid" without "or payable" is near zero early in a deal, and a shorter look-back shrinks the cap in proportion. Example: on $150k/yr billed monthly, a 12-month base gives $150k and a 3-month base gives $37.5k.
3. Confirm the other side's IP indemnity is uncapped, and that "indemnify" is not defined so broadly that first-party claims escape the cap.
