---
name: docx-redline
description: Write a redline of a contract. For a .docx, produces a copy with real Word tracked changes (insertions / deletions the other side can accept or reject) and margin comments; for a .txt / .md contract, produces a Markdown redline (~~deleted~~ **inserted**, comments as footnotes) ready to paste into an email. Use when the user asks for "a redline", "tracked changes", "a markup" or "comments in the doc"; not needed when they only want a list of issues.
---

# docx-redline

Standard library only. `docx_redline.py` sits next to this file.

```bash
H="$MANIGENT_AGENT_DIR/personal-skill-hub/skills/docx-redline/docx_redline.py"
python3 "$H" text CONTRACT.docx                      # numbered paragraphs
python3 "$H" apply CONTRACT.docx edits.json OUT.docx --author "Reviewer name"
python3 "$H" apply CONTRACT.txt edits.json OUT.md    # plain text in -> Markdown redline out
```

Plain-text paragraphs are blocks separated by a blank line (`text` shows the `[n]` index). In plain text a `find` may cross a line wrap inside its paragraph (any whitespace matches any whitespace), every `find` matches the original text rather than earlier markup, and an edit overlapping an earlier one is skipped.

## Steps

1. **Dump the text** with `text`. Review the contract (see the role's procedure; the
   `clause-extractor` skill helps). Decide every change before touching the file.
2. **Write `edits.json`**, one object per change, in document order:
   ```json
   [
     {"find": "exact current words", "replace": "new words", "comment": "why, citing the standard; fallback if refused", "para": 14},
     {"find": "words to flag only", "comment": "question or note, no text change"},
     {"find": "words to strike", "replace": ""}
   ]
   ```
   - `find` must be copied exactly from the `text` output and sit inside one paragraph.
     Keep it short but unique; add `para` (the `[n]` index) or `occurrence` when it repeats.
   - Change the fewest words that do the job. Replacing a whole clause makes the redline
     hard to read and invites a blanket rejection.
   - Comments go to the counterparty: professional, one or two sentences, cite the
     market standard (e.g. "Bonterms Cloud Terms §16: 12-month fees"), no internal strategy.
     Keep internal notes (walk-away points, what you will concede) in your chat reply.
3. **Apply** and read the summary line. Exit code 2 means some edits were skipped (text not
   found, or it crosses a tab / line break / field / the edge of a hyperlink). Fix `find` (shorter, or split into two
   edits) and re-run from the ORIGINAL file, never from a partly-redlined output.
4. **Verify** with `text OUT.docx`: the output shows the document as it would read with all
   changes accepted. Check every edit reads correctly in context.
5. **Deliver** OUT.docx (or paste OUT.md into your reply) plus a short cover note: list of changes by priority (must / should /
   nice), and the issues you raised by comment only.

## Limits

- Inserted text takes the formatting of the first run it replaces. Text inside a
  hyperlink can be edited, but one `find` cannot run from link text into plain text.
- Headers, footers, footnotes and text boxes are not edited.
- Existing tracked changes are left as they are; if the counterparty's draft already has
  open revisions, tell the user and ask whether to accept them first.
- To add a whole new clause, anchor on the last words of the preceding paragraph and
  replace them with themselves plus the new sentence(s).
