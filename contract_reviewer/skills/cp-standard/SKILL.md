---
name: cp-standard
description: Fetch the Common Paper Cloud Service Agreement (CSA) standard terms at the version a contract names (2.1, 3.0, ...), section by section, with the version read from the terms themselves and the source URL; detect which version a cover page or contract incorporates; and diff two versions section by section (removed, retitled, renumbered, changed). Use whenever an answer cites or compares against a Common Paper CSA section number or default, or a contract is "on Common Paper" - never cite a CP section from memory. Works offline on the vendored copies in knowledge/common-paper-csa/; the network mode is refused when MANIGENT_WEB_DISABLED=1.
---

# cp-standard

Common Paper publishes each CSA version as a new text, and section numbers and defaults
move between versions. A cover page incorporates ONE version, and that version's text is the
standard you review against. This skill fetches that text, so a citation like "§13.1" is
checked against the version the contract actually names.

```bash
H="$MANIGENT_AGENT_DIR/personal-skill-hub/skills/cp-standard/cp_standard.py"
```

## Commands

| Need | Command |
|---|---|
| Which CSA version a contract incorporates | `python3 $H detect CONTRACT.txt` (.txt / .md / .docx) |
| Text of a section at that version | `python3 $H section --version 2.1 --id 8.1 [--id 13.1]` |
| A whole article (heading and all subsections) | `python3 $H section --version 3.0 --id 8` |
| Section list | `python3 $H index --version 3.0` |
| What changed between versions | `python3 $H diff --from 2.1 --to 3.0 [--text]` |
| Released versions and the one on `main` | `python3 $H versions` |
| Offline | `--file knowledge/common-paper-csa/CSA-2.1.md` (or `CSA-3.0.md`); for diff, `--from-file` / `--to-file` |

## Reading the answer

- `version` is read from the terms' own "Standard Terms Version X" definition. `ref` is
  the git tag (released versions), the pinned commit (a version merged to `main` but not
  yet tagged: 3.0 is pinned to 3efceb0, the commit the offline copy was taken from), or
  `main` (any newer untagged version). `page_url` is the human-readable page to cite.
- Versions 2.0 and later only: tags 1.0 and 1.1 have no section anchors and fail with
  "no section anchors found". Contracts on 1.x are rare; read those terms by hand.
- diff statuses: `removed` (the clause is gone; its number may now hold another clause),
  `retitled`, `renumbered`, `changed`, `added`, or a combination such as
  `renumbered+changed`. Add `--text` to see the old and new wording.
- Two sections folded into one show as one `retitled` plus one `removed` (2.1 §9.1/§9.2
  -> 3.0 §9.1(a)/(b)). Read the new text before saying a clause was dropped: customer-side
  indemnity survives in 3.0 §9.1(b).

## Rules

1. **Use the version the contract names.** Run `detect` on the cover page or order form.
   If it names one version, cite that version's sections, even if a newer one exists.
2. **No version named:** say which you assumed, in one line. Before 3.0 is tagged on
   GitHub, assume the version on Common Paper's landing page (2.1 as of 2026-10-11), and
   name any 3.0 difference that would change the answer.
3. **Two versions named** (cover page says 2.1, attached terms say 3.0): flag it as an
   issue. It decides which defaults apply.
4. **Defaults differ by version.** In 2.1, §13.1 makes an undefined variable mean "none"
   and switches the clause off, so a struck General Cap Amount means no cap. 3.0 drops
   that rule. It keeps only a narrower one: with no Covered Claims defined there is no
   indemnity (§9.1(c)). Under 3.0, quote §8.1 and say the cap is undefined rather than
   reading it as "none". Run `section` before answering any "what if the cover page
   omits X" question.
5. **Web off:** with `MANIGENT_WEB_DISABLED=1`, use `--file` on the vendored copies, and
   say the text is as of the copy's commit (2.1: tag `2.1`; 3.0: `main` at 3efceb0,
   2026-09-30).

Exit status 2 with `error:` on stderr means the version, section or file could not be
resolved (a version that is neither a tag nor main's, a section that doesn't exist at that
version, or a file that isn't a CSA). Say so; never cite a section you could not fetch.
