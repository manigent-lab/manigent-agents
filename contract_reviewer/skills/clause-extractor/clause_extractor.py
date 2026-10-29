#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Manigent Contributors
"""Split a contract into clauses and tag each with playbook clause types.

    python3 clause_extractor.py CONTRACT [--format md|json]

CONTRACT may be .txt, .md or .docx (read with the standard library only).
A clause starts at a numbered heading ("1.", "1.1", "Section 4", "ARTICLE II",
"4.2(a)") or an all-caps heading line. Each clause gets zero or more tags from
TAGS below (keyword match, case-insensitive) plus flags for things that tend to
hide: operative language inside a definitions clause, one-party-only verbs,
"perpetual"/"survive" terms, and dollar/day/month numbers worth computing.
Tags are a reading aid, not a conclusion: read every clause anyway.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

TAGS: dict[str, list[str]] = {
    "definitions": [r"\bmeans\b", r"\bdefinitions?\b", r"\"[A-Z][^\"]+\"\s+(?:means|shall mean|includes)"],
    "confidentiality": [r"confidential", r"non-?disclosure"],
    "exclusions": [r"does not include", r"shall not include", r"\bexclusions?\b", r"publicly available", r"independently developed"],
    "residuals": [r"residual", r"unaided memory", r"retained in (?:the )?memory"],
    "return_destroy": [r"\breturn\b.*\bdestroy", r"destruction", r"\bdelete\b"],
    "term_survival": [r"\bterm\b", r"surviv", r"perpetu", r"indefinite"],
    "renewal": [r"renew", r"non-?renewal"],
    "price_change": [r"price increase", r"increase (?:the )?(?:fees|prices)", r"escalat", r"uplift", r"\bCPI\b"],
    "payment": [r"invoice", r"\bpayment\b", r"late (?:fee|charge)", r"\bnet \d+"],
    "limitation_of_liability": [r"limitation of liability", r"aggregate liability", r"shall not exceed", r"\bcap\b", r"consequential", r"lost profits"],
    "indemnity": [r"indemnif", r"hold harmless", r"defend"],
    "warranty": [r"warrant", r"as is"],
    "ip_ownership": [r"intellectual property", r"\bassigns?\b.*\b(?:right|title|interest)", r"work (?:made )?for hire", r"moral rights", r"pre-?existing", r"background"],
    "licence": [r"\blicen[cs]e", r"sublicens"],
    "feedback": [r"feedback", r"suggestions"],
    "data_protection": [r"personal data", r"process(?:or|ing)", r"sub-?processor", r"data protection", r"GDPR", r"CCPA", r"standard contractual clauses|\bSCCs?\b"],
    "security_breach": [r"security (?:incident|breach)", r"data breach", r"unauthori[sz]ed access"],
    "audit": [r"\baudit", r"inspect"],
    "assignment": [r"\bassign(?:ment)?\b(?!s? (?:all|its) right)", r"change of control", r"merger", r"acquisition"],
    "termination": [r"terminat"],
    # "exclusive" alone is usually venue/jurisdiction/remedy boilerplate, not a covenant.
    "restrictive_covenant": [r"non-?compet", r"not (?:to )?compete", r"non-?solicit", r"solicit", r"exclusivity",
                             r"exclusive (?:dealing|supplier|provider|vendor|customer|distribut|reseller|partner|arrangement|relationship|basis)"],
    "governing_law_venue": [r"governing law", r"governed by", r"jurisdiction", r"venue", r"arbitrat"],
    "insurance": [r"insurance"],
    "sla_support": [r"service level", r"\bSLA\b", r"uptime", r"availability", r"service credit"],
    "notices": [r"\bnotices?\b.*\b(?:writing|email|certified mail)"],
}

# Case-insensitive only for the "Section/Article/Clause N" keyword: the
# all-caps alternative must stay case-sensitive, or every short wrapped prose
# line ("the Customer, its affiliates and") would open a new clause.
HEADING_RE = re.compile(
    r"^\s*(?:(?i:section|article|clause)\s+[0-9IVXLCivxlc]+[.:]?|\d+(?:\.\d+)*[.)]?(?:\([a-z0-9]+\))?\s|\([a-z]\)\s|[A-Z][A-Z &/,'-]{3,}$)"
)
# Role labels that name whichever party is acting; in a mutual agreement they bind both sides.
ROLE_LABELS = frozenset({"Recipient", "Receiving Party"})
MUTUAL_ROLE_RE = re.compile(
    r"\b(?:each|either) party\b|\ba party (?:that|who|which) (?:receives|discloses)|\bthe party receiving\b"
    r"|\b(?:Recipient|Receiving Party)\W{0,3}\s+means\s+(?:a|any|each|either|the) party\b",
    re.IGNORECASE,
)
ONE_SIDED_RE = re.compile(r"\b(?:the )?(Recipient|Receiving Party|Customer|Vendor|Provider|Supplier|Consultant|Company|Contractor|Employee|Licensee|Licensor|Processor)\s+(?:shall|must|agrees to|will)\b")
NUMBER_RE = re.compile(r"\$\s?[\d,]+(?:\.\d+)?|\b\d+\s*(?:(?:days?|months?|years?|business days|hours|x|times)\b|%)|\(\d+\)\s*(?:days?|months?|years?)", re.IGNORECASE)


# Clause types a complete contract of each kind normally carries. A missing one
# is often the issue (no return/destroy in an NDA, no cap in an MSA). Excerpts
# legitimately lack most of them, so the report says "check", not "missing".
EXPECTED: dict[str, list[str]] = {
    "nda": ["confidentiality", "exclusions", "return_destroy", "term_survival"],
    "dpa": ["data_protection", "security_breach", "audit", "return_destroy"],
    "saas_msa": ["limitation_of_liability", "indemnity", "data_protection", "renewal", "termination",
                 "assignment", "governing_law_venue"],
    "services": ["ip_ownership", "licence", "limitation_of_liability", "termination", "governing_law_venue"],
    "employment": ["confidentiality", "restrictive_covenant", "governing_law_venue"],
}
KIND_RE = [
    ("dpa", r"data process\w* (?:addendum|agreement)|\bDPA\b|business associate"),
    ("nda", r"non-?disclosure|confidentiality agreement|\bNDA\b"),
    ("employment", r"offer letter|employment agreement|promotion|dear [A-Z]"),
    ("services", r"consulting|professional services|statement of work|independent contractor"),
    ("saas_msa", r"subscription|cloud|software[- ]as[- ]a[- ]service|\bSaaS\b|master (?:services|subscription)"),
]


def contract_kind(text: str) -> str | None:
    head = text[:600]
    for kind, pat in KIND_RE:
        if re.search(pat, head, re.IGNORECASE):
            return kind
    return None


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read("word/document.xml"))
        paras = []
        for p in root.iter(W + "p"):
            # w:t only: text inside tracked deletions (w:delText) is not current text.
            paras.append("".join(t.text or "" for t in p.iter(W + "t")))
        return "\n".join(paras)
    return path.read_text(encoding="utf-8", errors="replace")


def split_clauses(text: str) -> list[dict]:
    clauses: list[dict] = []
    current: dict | None = None
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if HEADING_RE.match(line) or current is None:
            current = {"start_line": lineno, "heading": line.strip()[:100], "text": line.strip()}
            clauses.append(current)
        else:
            current["text"] += "\n" + line.strip()
    return clauses


def tag_clause(c: dict, mutual_roles: bool = False) -> dict:
    """Tags, flags and numbers for one clause. ``mutual_roles``: the contract
    defines Recipient / Receiving Party as either party, so a clause binding
    only that role is not one-sided."""
    t = c["text"]
    tags = [name for name, pats in TAGS.items() if any(re.search(p, t, re.IGNORECASE) for p in pats)]
    flags = []
    if "definitions" in tags and len(tags) > 1:
        flags.append("definitions clause also matches operative tags: " + ", ".join(x for x in tags if x != "definitions"))
    actors = sorted({m.group(1) for m in ONE_SIDED_RE.finditer(t)})
    if len(actors) == 1 and not (mutual_roles and actors[0] in ROLE_LABELS):
        flags.append(f"obligation verbs bind only: {actors[0]} (check symmetry)")
    if re.search(r"perpetu|indefinite|in perpetuity", t, re.IGNORECASE):
        flags.append("perpetual / indefinite language")
    nums = NUMBER_RE.findall(t)
    return {**c, "tags": tags, "flags": flags, "numbers": nums[:12]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("contract")
    ap.add_argument("--format", choices=("md", "json"), default="md")
    args = ap.parse_args(argv)
    text = read_text(Path(args.contract))
    mutual_roles = bool(MUTUAL_ROLE_RE.search(text))
    clauses = [tag_clause(c, mutual_roles) for c in split_clauses(text)]
    if args.format == "json":
        json.dump(clauses, sys.stdout, indent=1)
        print()
        return 0
    print("| # | Line | Heading | Tags | Flags | Numbers |")
    print("|---|------|---------|------|-------|---------|")
    for i, c in enumerate(clauses, 1):
        cell = lambda s: s.replace("|", "/")  # noqa: E731
        print(f"| {i} | {c['start_line']} | {cell(c['heading'][:60])} | {', '.join(c['tags'])} | "
              f"{cell('; '.join(c['flags']))} | {cell(', '.join(c['numbers']))} |")
    untagged = [i for i, c in enumerate(clauses, 1) if not c["tags"]]
    if untagged:
        print(f"\nUntagged clauses (read closely): {untagged}")
    kind = contract_kind(text)
    if kind:
        present = {t for c in clauses for t in c["tags"]}
        absent = [t for t in EXPECTED[kind] if t not in present]
        if absent:
            print(f"\nContract type looks like: {kind}. No clause matched: {', '.join(absent)}. "
                  "Check whether each is really absent (a missing clause is often the issue) "
                  "or sits in a document you were not given.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
