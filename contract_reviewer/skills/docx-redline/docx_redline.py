#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Manigent Contributors
"""Read a .docx and write tracked-change redlines and margin comments.

Standard library only (zipfile + ElementTree): no python-docx needed, because
python-docx has no API for tracked changes (w:ins / w:del) anyway.

    python3 docx_redline.py text IN.docx
        Print every paragraph as "[n] text" (n is the paragraph index used by edits).

    python3 docx_redline.py apply IN.docx EDITS.json OUT.docx [--author NAME]
        Apply edits and write OUT.docx. EDITS.json is a list of objects:
          {"find": "exact text in one paragraph",       # required
           "replace": "new text",                       # omit for a comment-only edit; "" deletes
           "comment": "rationale shown in the margin",  # optional
           "para": 12,                                  # optional: restrict to paragraph n
           "occurrence": 1}                             # optional: nth match in that paragraph
        Each edit becomes <w:del> of the found text + <w:ins> of the new text, so
        the counterparty sees a normal Word redline they can accept or reject.

    IN may also be plain text (.txt / .md). Paragraphs are blocks separated by
    a blank line; `apply` then writes a Markdown redline to OUT (deletions as
    ~~struck~~, insertions as **bold**, comments as numbered footnotes) that can
    be pasted into an email or chat. Every "find" is matched against the
    original text (never against markup an earlier edit added; overlapping
    edits are refused), and whitespace in "find" matches any whitespace run,
    so a phrase may cross a line wrap inside its paragraph.

Limits: "find" must sit inside one paragraph and must not span a tab, line
break, field, image or the edge of a hyperlink (text inside a hyperlink is
editable); an edit that cannot be placed is reported and skipped
(exit code 2), the rest are still written. Text in tables is covered (table
cells are paragraphs); headers, footers and footnotes are not.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{%s}" % W_NS
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
COMMENTS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
COMMENTS_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"


def _register_namespaces(xml: str) -> None:
    for prefix, uri in re.findall(r'xmlns:(\w+)="([^"]+)"', xml):
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            pass


def _serialize(root: ET.Element, original_xml: str) -> bytes:
    """ElementTree drops unused xmlns declarations, which breaks mc:Ignorable;
    restore the original root start tag so every declared prefix survives."""
    out = ET.tostring(root, encoding="unicode")
    orig_tag = re.search(r"<w:document\b[^>]*>|<w:comments\b[^>]*>", original_xml)
    if orig_tag:
        out = re.sub(r"<w:(document|comments)\b[^>]*>", lambda m: orig_tag.group(0), out, count=1)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + out).encode("utf-8")


# Run children that carry no text and may be dropped when a run is rewritten.
# w:lastRenderedPageBreak is a layout cache Word writes into ordinary runs.
_IGNORABLE_IN_RUN = frozenset({W + "rPr", W + "lastRenderedPageBreak"})
# Paragraph children whose w:r children are ordinary, editable text.
_RUN_CONTAINERS = frozenset({W + "hyperlink", W + "smartTag"})


def _run_text(r: ET.Element) -> str | None:
    """Text of a plain run, or None if it holds anything besides rPr / t
    (and the ignorable layout markers above)."""
    parts = []
    for child in r:
        if child.tag in _IGNORABLE_IN_RUN:
            continue
        if child.tag != W + "t":
            return None
        parts.append(child.text or "")
    return "".join(parts)


def _runs(p: ET.Element) -> list[tuple[ET.Element, ET.Element]]:
    """(parent, run) for every current-text run of ``p``, in order: direct
    runs and runs inside a hyperlink or smart tag. Runs inside w:del (deleted
    text) and w:ins (someone else's open insertion) are skipped."""
    out = []
    for child in p:
        if child.tag == W + "r":
            out.append((p, child))
        elif child.tag in _RUN_CONTAINERS:
            out.extend((child, r) for r in child if r.tag == W + "r")
    return out


def paragraphs(doc_root: ET.Element) -> list[ET.Element]:
    return list(doc_root.iter(W + "p"))


def para_text(p: ET.Element) -> str:
    return "".join(t.text or "" for t in p.iter(W + "t"))


def _mk_run(rpr: ET.Element | None, text: str, deleted: bool = False) -> ET.Element:
    r = ET.Element(W + "r")
    if rpr is not None:
        r.append(copy.deepcopy(rpr))
    t = ET.SubElement(r, W + ("delText" if deleted else "t"))
    t.text = text
    t.set(XML_SPACE, "preserve")
    return r


class Redliner:
    def __init__(self, doc_root: ET.Element, author: str):
        self.root = doc_root
        self.author = author
        self.date = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ids = [int(v) for e in doc_root.iter() for k, v in e.attrib.items() if k == W + "id" and v.isdigit()]
        self.next_id = max(ids, default=0) + 1000
        self.comments: list[tuple[int, str]] = []

    def _id(self) -> str:
        self.next_id += 1
        return str(self.next_id)

    def apply(self, edit: dict) -> str | None:
        """Apply one edit; return an error string or None."""
        find = edit.get("find") or ""
        if not find:
            return "empty 'find'"
        paras = paragraphs(self.root)
        cands = [paras[edit["para"]]] if "para" in edit else paras
        occurrence = int(edit.get("occurrence", 1))
        for p in cands:
            pairs = _runs(p)
            runs = [r for _, r in pairs]
            texts = [_run_text(r) for r in runs]
            joined, spans, pos = "", [], 0
            for r, t in zip(runs, texts):
                t = t or ""
                spans.append((pos, pos + len(t)))
                joined += t
                pos += len(t)
            idx, start = -1, 0
            for _ in range(occurrence):
                idx = joined.find(find, start)
                if idx < 0:
                    break
                start = idx + 1
            if idx < 0:
                continue
            end = idx + len(find)
            hit = [i for i, (a, b) in enumerate(spans) if a < end and b > idx]
            if any(texts[i] is None for i in hit):
                return f"'{find[:40]}' spans a tab, break, field or image"
            parents = {id(pairs[i][0]) for i in hit}
            if len(parents) > 1:
                return f"'{find[:40]}' crosses a hyperlink boundary; split it into two edits"
            self._rewrite(pairs[hit[0]][0], runs, texts, spans, hit, idx, end, edit)
            return None
        return f"'{find[:40]}' not found" + (f" in paragraph {edit['para']}" if "para" in edit else "")

    def _rewrite(self, parent, runs, texts, spans, hit, idx, end, edit) -> None:
        first, last = runs[hit[0]], runs[hit[-1]]
        rpr_first = first.find(W + "rPr")
        rpr_last = last.find(W + "rPr")
        new: list[ET.Element] = []
        pre = texts[hit[0]][: idx - spans[hit[0]][0]]
        post = texts[hit[-1]][end - spans[hit[-1]][0]:]
        if pre:
            new.append(_mk_run(rpr_first, pre))
        cid = None
        if edit.get("comment"):
            cid = str(len(self.comments) + self._comment_base())
            new.append(ET.Element(W + "commentRangeStart", {W + "id": cid}))
        replace = edit.get("replace")
        pieces = []
        for i in hit:
            a, b = spans[i]
            pieces.append((runs[i].find(W + "rPr"), texts[i][max(idx, a) - a: min(end, b) - a]))
        if replace is None:
            new.extend(_mk_run(rpr, t) for rpr, t in pieces if t)
        else:
            d = ET.Element(W + "del", {W + "id": self._id(), W + "author": self.author, W + "date": self.date})
            d.extend(_mk_run(rpr, t, deleted=True) for rpr, t in pieces if t)
            new.append(d)
            if replace:
                ins = ET.Element(W + "ins", {W + "id": self._id(), W + "author": self.author, W + "date": self.date})
                ins.append(_mk_run(rpr_first, replace))
                new.append(ins)
        if cid is not None:
            new.append(ET.Element(W + "commentRangeEnd", {W + "id": cid}))
            ref = ET.Element(W + "r")
            ET.SubElement(ET.SubElement(ref, W + "rPr"), W + "rStyle", {W + "val": "CommentReference"})
            ET.SubElement(ref, W + "commentReference", {W + "id": cid})
            new.append(ref)
            self.comments.append((int(cid), edit["comment"]))
        if post:
            new.append(_mk_run(rpr_last, post))
        pos = list(parent).index(first)
        for i in hit:
            parent.remove(runs[i])
        for k, el in enumerate(new):
            parent.insert(pos + k, el)

    _base: int | None = None

    def _comment_base(self) -> int:
        if self._base is None:
            ids = [int(e.get(W + "id")) for e in self.root.iter(W + "commentReference") if (e.get(W + "id") or "").isdigit()]
            self._base = max(ids, default=-1) + 1
        return self._base


def _add_comments(files: dict[str, bytes], comments, author: str, date: str) -> None:
    name = "word/comments.xml"
    if name in files:
        cxml = files[name].decode("utf-8")
        _register_namespaces(cxml)
        croot = ET.fromstring(cxml)
    else:
        cxml = f'<w:comments xmlns:w="{W_NS}">'
        croot = ET.Element(W + "comments")
        # Package parts are edited as text so their default namespaces stay untouched.
        rels_name = "word/_rels/document.xml.rels"
        rels = files[rels_name].decode("utf-8")
        ids = [int(n) for n in re.findall(r'Id="rId(\d+)"', rels)]
        rel = (f'<Relationship Id="rId{max(ids, default=0) + 1}" Type="{COMMENTS_REL}" '
               'Target="comments.xml"/>')
        files[rels_name] = rels.replace("</Relationships>", rel + "</Relationships>").encode("utf-8")
        ct = files["[Content_Types].xml"].decode("utf-8")
        if "/word/comments.xml" not in ct:
            ov = f'<Override PartName="/word/comments.xml" ContentType="{COMMENTS_CT}"/>'
            files["[Content_Types].xml"] = ct.replace("</Types>", ov + "</Types>").encode("utf-8")
    initials = "".join(w[0] for w in author.split()[:3]).upper() or "R"
    for cid, text in comments:
        c = ET.SubElement(croot, W + "comment", {W + "id": str(cid), W + "author": author, W + "date": date, W + "initials": initials})
        for line in text.split("\n"):
            ET.SubElement(c, W + "p").append(_mk_run(None, line))
    files[name] = _serialize(croot, cxml)


_PLAIN = (".txt", ".md", ".markdown", ".text")


def _is_plain(path: str) -> bool:
    return path.lower().endswith(_PLAIN)


def _plain_paragraphs(text: str) -> list[str]:
    """Blocks separated by blank lines, internal line breaks kept."""
    return [b.strip("\n") for b in re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n")) if b.strip()]


def _plain_find(para: str, find: str) -> list[tuple[int, int]]:
    """(start, end) of each non-overlapping match of ``find`` in ``para``, where
    any whitespace run in either (a line wrap included) matches any other."""
    words = find.split()
    if not words:
        return []
    pat = r"\s+".join(map(re.escape, words))
    return [m.span() for m in re.finditer(pat, para)]


def _plain_apply(paras: list[str], edit: dict, notes: list[str],
                 spans: dict[int, list[tuple[int, int, str]]]) -> str | None:
    """Place one edit against the ORIGINAL paragraph text and record it in
    ``spans`` ({para: [(start, end, markup)]}); None on success. Matching never
    sees earlier markup, and an edit overlapping an earlier one is refused."""
    find = edit.get("find") or ""
    if not find.strip():
        return "empty find"
    want = edit.get("occurrence", 1)
    idxs = [edit["para"]] if "para" in edit else range(len(paras))
    seen = 0
    for i in idxs:
        if not 0 <= i < len(paras):
            return f"para {i} out of range"
        for start, end in _plain_find(paras[i], find):
            seen += 1
            if seen != want:
                continue
            if any(start < e and s < end for s, e, _ in spans.get(i, [])):
                return "overlaps an earlier edit"
            old = " ".join(paras[i][start:end].split())
            mark = ""
            if edit.get("comment"):
                notes.append(edit["comment"])
                mark = f"[^{len(notes)}]"
            if "replace" not in edit:
                new = f"=={old}=={mark}"
            elif edit["replace"] == "":
                new = f"~~{old}~~{mark}"
            else:
                new = f"~~{old}~~ **{edit['replace']}**{mark}"
            spans.setdefault(i, []).append((start, end, new))
            return None
    return "text not found" if seen == 0 else f"only {seen} occurrence(s)"


def _plain_render(paras: list[str], spans: dict[int, list[tuple[int, int, str]]]) -> list[str]:
    out = []
    for i, p in enumerate(paras):
        for s, e, new in sorted(spans.get(i, []), reverse=True):
            p = p[:s] + new + p[e:]
        out.append(p)
    return out


def cmd_plain_apply(src: str, edits_path: str, dst: str) -> int:
    edits = json.load(open(edits_path, encoding="utf-8"))
    paras = _plain_paragraphs(open(src, encoding="utf-8").read())
    notes: list[str] = []
    spans: dict[int, list[tuple[int, int, str]]] = {}
    failed = 0
    for n, e in enumerate(edits, 1):
        err = _plain_apply(paras, e, notes, spans)
        if err:
            failed += 1
            print(f"edit {n}: SKIPPED - {err}", file=sys.stderr)
    body = "\n\n".join(_plain_render(paras, spans))
    if notes:
        body += "\n\n" + "\n".join(f"[^{k}]: {c}" for k, c in enumerate(notes, 1))
    open(dst, "w", encoding="utf-8").write(body + "\n")
    print(f"wrote {dst}: {len(edits) - failed} applied, {failed} skipped, {len(notes)} comment(s)")
    return 2 if failed else 0


def cmd_text(path: str) -> int:
    if _is_plain(path):
        for i, t in enumerate(_plain_paragraphs(open(path, encoding="utf-8").read())):
            print(f"[{i}] {t}")
        return 0
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    for i, p in enumerate(paragraphs(root)):
        t = para_text(p)
        if t.strip():
            print(f"[{i}] {t}")
    return 0


def cmd_apply(src: str, edits_path: str, dst: str, author: str) -> int:
    edits = json.load(open(edits_path, encoding="utf-8"))
    with zipfile.ZipFile(src) as z:
        files = {n: z.read(n) for n in z.namelist()}
        doc_xml = files["word/document.xml"].decode("utf-8")
        _register_namespaces(doc_xml)
        root = ET.fromstring(doc_xml)
        rl = Redliner(root, author)
        failed = 0
        for n, e in enumerate(edits, 1):
            err = rl.apply(e)
            if err:
                failed += 1
                print(f"edit {n}: SKIPPED - {err}", file=sys.stderr)
        files["word/document.xml"] = _serialize(root, doc_xml)
        if rl.comments:
            _add_comments(files, rl.comments, author, rl.date)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as out:
        if "[Content_Types].xml" in files:
            out.writestr("[Content_Types].xml", files.pop("[Content_Types].xml"))
        for n, data in files.items():
            out.writestr(n, data)
    print(f"wrote {dst}: {len(edits) - failed} applied, {failed} skipped, {len(rl.comments)} comment(s)")
    return 2 if failed else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("text")
    t.add_argument("docx")
    a = sub.add_parser("apply")
    a.add_argument("docx")
    a.add_argument("edits")
    a.add_argument("out")
    a.add_argument("--author", default="Contract Reviewer")
    args = ap.parse_args(argv)
    if args.cmd == "text":
        return cmd_text(args.docx)
    if _is_plain(args.docx):
        return cmd_plain_apply(args.docx, args.edits, args.out)
    return cmd_apply(args.docx, args.edits, args.out, args.author)


if __name__ == "__main__":
    sys.exit(main())
