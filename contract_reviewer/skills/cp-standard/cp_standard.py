#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Manigent Contributors
"""Common Paper Cloud Service Agreement standard terms, fetched at the version a contract names.

    python cp_standard.py versions
    python cp_standard.py detect contract.docx
    python cp_standard.py section --version 2.1 --id 8.1 [--id 13.1] [--file saved-CSA.md]
    python cp_standard.py index   --version 3.0 [--file saved-CSA.md]
    python cp_standard.py diff    --from 2.1 --to 3.0 [--from-file a.md] [--to-file b.md] [--text]

Every answer is JSON and carries `version` (read from the terms' own "Standard Terms
Version X" definition, not assumed), `ref` (the git tag or branch it came from) and
`source_url`.

Rules applied:
  * The version is the one the CONTRACT names. A version is looked up as a git tag in
    github.com/CommonPaper/CSA first; if there is no such tag, at the commit pinned in
    PINNED (a version merged to main but not yet tagged); otherwise on `main`, accepted
    only if main's own text says it is that version. `ref` reports which one answered.
    Tags 1.0 and 1.1 use plain headings with no section anchors, so 2.0 is the oldest
    version this skill can parse.
  * Section ids are Common Paper's own anchors (`id="8.1"`). Asking for a top-level id
    ("8") returns the heading and every subsection under it.
  * diff pairs sections by heading, not by number, so a clause that moved (Taxes 4.4 ->
    4.2) is reported as renumbered, and a clause whose number now holds something else
    (13.1 "Defining Variables" -> 13.1 "Affiliate") is reported as removed.

Online fetches are refused when MANIGENT_WEB_DISABLED is 1 / true / yes; pass a saved
CSA.md with --file / --from-file / --to-file instead. Stdlib only.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

WEB_DISABLED_ENV = "MANIGENT_WEB_DISABLED"
UA = "Manigent contract_reviewer (cp-standard skill)"

RAW_URL = "https://raw.githubusercontent.com/CommonPaper/CSA/{ref}/CSA.md"
PAGE_URL = "https://commonpaper.com/standards/cloud-service-agreement/{version}"
# git's own ref advertisement: lists tags without the REST API's 60-requests-an-hour limit.
TAGS_URL = "https://github.com/CommonPaper/CSA.git/info/refs?service=git-upload-pack"
CURRENT_REF = "main"
# Versions merged to main before Common Paper tagged them, pinned to the commit the vendored
# copy in knowledge/common-paper-csa/ was taken from, so live and offline answers agree.
PINNED = {"3.0": "3efceb01e3c8bfb7b302a5f34975aa2b084026a3"}

_ID_RE = re.compile(r'id="(\d+(?:\.\d+)*)">(.*?)</span>')
_VERSION_RE = re.compile(r"Standard Terms,?\s+Version\s+(\d+(?:\.\d+)?)", re.I)
# How a contract names the CSA it incorporates: "Cloud Service Agreement ... Version 2.1"
# or "CSA v3.0" on a cover page, or "Standard Terms Version 3.0" in a definition. A bare
# "CSA" must be followed directly by its version, so "the CSA CCM v4.0" (Cloud Security
# Alliance) is not read as a CSA version. After the full name, a defined-term aside such
# as (the "Agreement") is skipped, and the gap to the version stops at another document's
# name, so "... Cloud Service Agreement and the DPA Version 1.1" is not read as CSA 1.1.
_CONTRACT_RE = re.compile(
    r"\bCSA\s*,?\s*v(?:ersion)?\.?\s*(\d+\.\d+)\b"
    r"|\bCloud\s+Service\s+Agreement(?:\s*\([^)\n]{0,40}\))?"
    r"(?:(?!\b(?:DPA|NDA|BAA|Addendum|Agreement)\b)[^\n]){0,40}?"
    r"\bv(?:ersion)?\.?\s*(\d+\.\d+)\b"
    r"|Standard\s+Terms,?\s+Version\s+(\d+(?:\.\d+)?)", re.I)


class InputError(Exception):
    pass


class NotFound(InputError):
    """HTTP 404: the ref (tag or commit) does not exist."""


def web_disabled() -> bool:
    """Network modes are off when MANIGENT_WEB_DISABLED is set, unless the eval
    network gate (below) admits this reviewed wrapper."""
    if net_gate():
        return False
    return os.environ.get(WEB_DISABLED_ENV, "").strip().lower() in ("1", "true", "yes")


# ---------------------------------------------------------------- eval network gate
# Inert unless the eval harness sets MANIGENT_NET_LOG and MANIGENT_NET_TOKEN
# (evals/runner.py, specialist arm). Then this script is one of the reviewed
# wrappers allowed to reach the network: it bypasses the dead HTTP(S)_PROXY the
# harness gives every other shell process, refuses any host outside
# APPROVED_HOSTS (redirect targets included), and appends one JSONL record per
# start and per request to the log the harness checks after the run.
WRAPPER = "cp_standard"
APPROVED_HOSTS = frozenset({"raw.githubusercontent.com", "commonpaper.com", "github.com"})
NET_LOG_ENV = "MANIGENT_NET_LOG"
NET_TOKEN_ENV = "MANIGENT_NET_TOKEN"
_net_operation = ""


def net_gate() -> bool:
    return bool(os.environ.get(NET_LOG_ENV) and os.environ.get(NET_TOKEN_ENV))


def net_record(event: str, host: str | None, ok: bool, detail: str = "") -> None:
    if not net_gate():
        return
    rec = {"wrapper": WRAPPER, "operation": _net_operation, "event": event, "host": host, "ok": ok,
           "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "token": os.environ[NET_TOKEN_ENV], "detail": detail[:300]}
    with open(os.environ[NET_LOG_ENV], "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def net_start(operation: str) -> None:
    global _net_operation
    _net_operation = operation
    net_record("start", None, True)


def _approved_host(url: str) -> str:
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    if host not in APPROVED_HOSTS:
        net_record("refused", host, False, url)
        raise urllib.error.URLError(f"{host} is not an approved host for {WRAPPER}")
    return host


class _ApprovedRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _approved_host(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def net_open(req: urllib.request.Request, timeout: float):
    """urllib.request.urlopen, through the eval network gate when it is on."""
    if not net_gate():
        return urllib.request.urlopen(req, timeout=timeout)
    host = _approved_host(req.full_url)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _ApprovedRedirects)
    try:
        resp = opener.open(req, timeout=timeout)
    except Exception as e:
        net_record("request", host, False, f"{type(e).__name__}: {e}")
        raise
    net_record("request", host, True, req.full_url)
    return resp


def http_get(url: str) -> str:
    if web_disabled():
        raise InputError(f"{WEB_DISABLED_ENV} is set; pass a saved CSA.md with --file")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with net_open(req, timeout=30) as resp:
            return resp.read().decode("utf-8-sig")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise NotFound(f"HTTP 404 for {url}") from exc
        raise InputError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise InputError(f"cannot reach {url}: {exc.reason}") from exc


def _plain(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).replace("**", "")


def _heading(raw: str) -> str:
    return _plain(raw).strip().strip('"').strip().rstrip(".").strip()


def parse_terms(text: str) -> dict:
    """CSA.md -> {"version", "sections": {id: {"heading", "text"}}} in document order.

    A section's text runs from its anchor line to the next anchor, so lettered sub-items
    (8.1(a), 8.1(b)) stay with their parent.
    """
    sections: dict[str, dict] = {}
    cur = None
    for line in text.splitlines():
        m = _ID_RE.search(line)
        if m:
            cur = m.group(1)
            body = _plain(line[m.end():]).strip()
            sections[cur] = {"heading": _heading(m.group(2)), "lines": [body] if body else []}
        elif cur and line.strip():
            sections[cur]["lines"].append(_plain(line).strip())
    if not sections:
        raise InputError("no section anchors found; this is not a Common Paper CSA.md "
                         "(or its layout changed)")
    found = _VERSION_RE.search(_plain(text))
    out = {id_: {"heading": s["heading"], "text": "\n".join(s["lines"])} for id_, s in sections.items()}
    return {"version": found.group(1) if found else None, "sections": out}


def load(version: str | None = None, file: str | None = None) -> dict:
    """The terms for `version` (from a saved file, a release tag, or main) with provenance."""
    if file:
        terms = parse_terms(Path(file).read_text(encoding="utf-8-sig"))
        if version and terms["version"] and terms["version"] != version:
            raise InputError(f"{file} is version {terms['version']}, not {version}")
        terms.update(ref="file", source_url=str(Path(file).resolve()))
        return terms
    if not version:
        raise InputError("pass --version (the one the contract names) or --file")
    for ref in (version, PINNED.get(version), CURRENT_REF):
        if not ref:
            continue
        url = RAW_URL.format(ref=ref)
        try:
            terms = parse_terms(http_get(url))
        except NotFound:
            continue
        if terms["version"] == version:
            break
        if ref != CURRENT_REF:
            raise InputError(f"{url} says it is version {terms['version']}, not {version}")
        raise InputError(f"version {version} is not a release tag and {CURRENT_REF} is version "
                         f"{terms['version']}")
    else:
        raise InputError(f"no tag or branch found for version {version}")
    terms.update(ref=ref, source_url=url, page_url=PAGE_URL.format(version=version))
    return terms


def _meta(terms: dict) -> dict:
    return {k: terms[k] for k in ("version", "ref", "source_url", "page_url") if k in terms}


def section(terms: dict, ids: list[str]) -> dict:
    out = []
    for want in ids:
        hits = [(i, s) for i, s in terms["sections"].items() if i == want or i.startswith(want + ".")]
        if not hits:
            raise InputError(f"no section {want} in version {terms['version']}")
        out.append({"id": want, "heading": hits[0][1]["heading"],
                    "text": "\n".join(f"{i} {s['heading']}. {s['text']}".strip() if i != want else s["text"]
                                      for i, s in hits).strip()})
    return {**_meta(terms), "sections": out}


def index(terms: dict) -> dict:
    return {**_meta(terms), "sections": [{"id": i, "heading": s["heading"]} for i, s in terms["sections"].items()]}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def diff(old: dict, new: dict, with_text: bool = False) -> dict:
    """Section-level changes from `old` to `new`, paired by heading (leaf sections only)."""
    def leaves(t):
        ids = list(t["sections"])
        return [(i, t["sections"][i]) for i in ids if not any(j.startswith(i + ".") for j in ids)]

    def status(moved: bool, same_text: bool, kind: str = "renumbered") -> str:
        return kind if same_text else (f"{kind}+changed" if moved else "changed")

    by_heading: dict[str, list] = {}
    for i, s in leaves(new):
        by_heading.setdefault(s["heading"].lower(), []).append((i, s))
    # A heading can appear twice (the "Fees" section and the "Fees" definition), so pair in
    # passes across the whole text: same id first, then same article, then document order.
    old_leaves = leaves(old)
    paired: dict[str, tuple] = {}
    for same in (lambda i, j: i == j, lambda i, j: i.split(".")[0] == j.split(".")[0], lambda i, j: True):
        for i, s in old_leaves:
            match = by_heading.get(s["heading"].lower(), [])
            k = next((k for k, (j, _) in enumerate(match) if same(i, j)), None) if i not in paired else None
            if k is not None:
                paired[i] = match.pop(k)
    changes = []
    for i, s in old_leaves:
        if i not in paired:
            changes.append({"status": "removed", "from_id": i, "heading": s["heading"], "from_text": s["text"]})
            continue
        j, t = paired[i]
        same_text = _norm(s["text"]) == _norm(t["text"])
        if i != j or not same_text:
            changes.append({"status": status(i != j, same_text), "from_id": i, "to_id": j,
                            "heading": s["heading"], "from_text": s["text"], "to_text": t["text"]})
    # A removed heading whose number now holds an unmatched new heading was retitled
    # ("Liability Caps" -> "Liability Cap"), not removed and re-added.
    unmatched = {j: t for rest in by_heading.values() for j, t in rest}
    for entry in changes:
        t = unmatched.pop(entry["from_id"], None) if entry["status"] == "removed" else None
        if t is not None:
            same_text = _norm(entry["from_text"]) == _norm(t["text"])
            entry.update(status=status(True, same_text, "retitled"), to_id=entry["from_id"],
                         to_heading=t["heading"], to_text=t["text"])
    for j, t in unmatched.items():
        changes.append({"status": "added", "to_id": j, "heading": t["heading"], "to_text": t["text"]})
    for entry in changes:
        if not with_text or entry.get("from_text") == entry.get("to_text"):
            entry.pop("from_text", None)
            entry.pop("to_text", None)
    return {"from": _meta(old), "to": _meta(new), "changes": changes}


def contract_text(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".docx":
        with zipfile.ZipFile(p) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        xml = re.sub(r"</w:p>", "\n", xml)
        xml = re.sub(r"<w:(?:tab|br|cr)\b[^>]*/>", " ", xml)
        return html.unescape(re.sub(r"<[^>]+>", "", xml))
    return p.read_text(encoding="utf-8-sig", errors="replace")


def detect(path: str) -> dict:
    """Which CSA version(s) a contract names. Several distinct versions is itself an issue."""
    text = contract_text(path)
    hits = []
    for m in _CONTRACT_RE.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        hits.append({"version": m.group(1) or m.group(2) or m.group(3), "line": line, "quote": _norm(m.group(0))})
    versions = sorted({h["version"] for h in hits})
    return {"file": path, "versions": versions, "mentions": hits,
            "note": (None if len(versions) == 1 else
                     "no CSA version named; ask which one, or say which you assumed" if not versions else
                     "the contract names more than one CSA version; flag it")}


def versions() -> dict:
    tags = sorted(set(re.findall(r"refs/tags/([^\s^]+)", http_get(TAGS_URL))),
                  key=lambda v: [int(x) for x in re.findall(r"\d+", v)])
    current = parse_terms(http_get(RAW_URL.format(ref=CURRENT_REF)))["version"]
    return {"tagged": tags, "pinned_untagged": dict(PINNED), "current_on_main": current,
            "untagged_current": current if current not in tags else None}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("versions", help="released tags and the version on main")
    d = sub.add_parser("detect", help="which CSA version a contract (.txt/.md/.docx) names")
    d.add_argument("path")
    s = sub.add_parser("section", help="text of one or more sections at a version")
    s.add_argument("--id", action="append", required=True, dest="ids")
    i = sub.add_parser("index", help="section ids and headings at a version")
    for x in (s, i):
        x.add_argument("--version")
        x.add_argument("--file", help="saved CSA.md (offline)")
    f = sub.add_parser("diff", help="section-level changes between two versions")
    f.add_argument("--from", dest="old", required=True)
    f.add_argument("--to", dest="new", required=True)
    f.add_argument("--from-file")
    f.add_argument("--to-file")
    f.add_argument("--text", action="store_true", help="include old and new text of changed sections")
    a = p.parse_args(argv)
    net_start(a.cmd)
    try:
        if a.cmd == "versions":
            out = versions()
        elif a.cmd == "detect":
            out = detect(a.path)
        elif a.cmd == "section":
            out = section(load(a.version, a.file), a.ids)
        elif a.cmd == "index":
            out = index(load(a.version, a.file))
        else:
            out = diff(load(a.old, a.from_file), load(a.new, a.to_file), a.text)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
