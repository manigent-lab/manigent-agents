---
name: clause-extractor
description: Split a contract (.txt, .md, pasted text saved to a file, or .docx) into numbered clauses, tag each with its playbook clause type (confidentiality, residuals, cap, indemnity, IP, data protection, renewal, assignment, restrictive covenant, law/venue...), flag one-sided obligations, perpetual terms and operative language hiding in definitions, and list the clause types a complete contract of that kind would carry but this one lacks (e.g. an NDA with no return/destroy clause). Use when asked to review a whole contract (any length); skip it for a single-clause or closed question.
---

# clause-extractor

A systematic first pass. The helper does the splitting and keyword tagging; you do the reading.

## Steps

1. Run the helper on the contract file (stdlib only, no install; plain text works as well as .docx):
   ```bash
   python3 "$MANIGENT_AGENT_DIR/personal-skill-hub/skills/clause-extractor/clause_extractor.py" CONTRACT.docx
   # --format json for machine use
   ```
   If the contract was pasted into chat, save it to a .txt file first.
2. Read the table. For every clause:
   - map each tag to the learnings file that covers it (`memory/learnings/INDEX.md`);
   - note **flags**: a definitions clause that also matches operative tags (a carve-out
     or licence right hidden in a definition), obligation verbs that bind only one
     party, perpetual / indefinite language;
   - list the **numbers** (caps, look-back periods, notice days, multiples) to compute later.
3. Read every **untagged** clause in full. Keyword tagging misses unusual drafting.
4. Check for **absences**. The last line of the output names expected clause types no clause
   matched; confirm each by reading (an excerpt legitimately lacks most of them, so only a
   complete document's gaps are issues). Build the expected clause list for the contract type
   (NDA: definition, exclusions, use, compelled disclosure, return/destroy, term; SaaS MSA:
   cap, indemnity, IP, data, renewal, termination, assignment, law; DPA: the Art. 28(3)
   checklist; services: IP ownership, background IP, licence-back). A missing clause is often
   the issue.
5. Classify each material clause Standard / Fallback / Deviation / Walk-away and carry the
   result into your answer. Do not mention the tool or paste its table unless asked.

## Limits

- Heading detection is heuristic. If a clause list looks wrong (one giant clause, or
  every line a clause), read the contract directly and split by hand.
- Tables, footnotes and text boxes in .docx are not read. Check them separately.
- Tags are hints. A clause tagged `limitation_of_liability` may still be missing a carve-out.
