#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Manigent Contributors
"""Fetch SEC EDGAR XBRL data and turn companyfacts JSON into clean time series.

Offline (no network; works on a saved companyfacts or companyconcept JSON):
    python edgar_facts.py tags    --facts cf.json [--grep Revenue]
    python edgar_facts.py series  --facts cf.json --tag Revenues [--taxonomy us-gaap]
                                  [--unit USD] [--period annual|quarterly|ytd|instant|any]
                                  [--mode latest|frame] [--forms 10-K,10-Q] [--derive-q4]
    python edgar_facts.py history --facts cf.json [--freq annual|quarterly] [--wide]
                                  [--format csv|json] [--out hist.csv]

Online (data.sec.gov / www.sec.gov). Needs a User-Agent with a contact e-mail, from
--user-agent or $SEC_USER_AGENT (e.g. "Acme Research ops@acme.com"). Throttled below
SEC's 10 requests/s. Refused when MANIGENT_WEB_DISABLED is 1 / true / yes.
    python edgar_facts.py fetch companyfacts --cik 320193 --out cf.json
    python edgar_facts.py fetch concept --cik 320193 --tag AccountsPayableCurrent --out c.json
    python edgar_facts.py fetch frames --tag AccountsPayableCurrent --unit USD --period CY2025Q4I
    python edgar_facts.py fetch submissions --cik 320193 --out sub.json
    python edgar_facts.py cik --ticker AAPL [--tickers-file company_tickers.json]

Rules applied (see memory/learnings/xbrl-dedupe-and-periods.md):
  * fy / fp belong to the FILING, not to the data period. They are never used as a key.
    The period is (start, end) for duration facts and end for instants.
  * Duplicates of one period keep the row with the latest `filed` (restatements win).
    --mode frame keeps only rows that carry `frame` (SEC tags only the last-filed fact
    that best fits a calendar period), for calendar-aligned series.
  * Period length is classified from end - start in days, never from fp.
  * Q4 is derived (FY minus 9-month YTD, else FY minus Q1..Q3) for flow items only.
  * Unit arrays are never summed together. companyfacts keys "USD/shares"; the frames
    URL needs "USD-per-shares" (converted automatically).
  * Values are full units as filed (not thousands); signs are the concept's natural
    balance (capex is positive). Apply model signs downstream.

Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from datetime import date, timedelta
from pathlib import Path

WEB_DISABLED_ENV = "MANIGENT_WEB_DISABLED"
UA_ENV = "SEC_USER_AGENT"
DATA_SEC = "https://data.sec.gov"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
MAX_REQ_PER_SEC = 8.0  # SEC fair access ceiling is 10/s; stay under it
THROTTLE_FILE_ENV = "EDGAR_THROTTLE_FILE"

PERIOD_TYPES = ("annual", "quarterly", "ytd", "instant", "other")
DEFAULT_FORMS = ("10-K", "10-K/A", "10-Q", "10-Q/A", "20-F", "20-F/A", "40-F", "40-F/A",
                 "10-KT", "10-KT/A", "10-QT", "10-QT/A")
ANNUAL_FORMS = ("10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A", "10-KT", "10-KT/A")

# line item -> (kind, unit, [taxonomy:tag in priority order]). The first tag that has a
# value for a period wins (newest tag preferred where tags overlap).
LINE_ITEMS: list[tuple[str, str, str, list[str]]] = [
    ("revenue", "flow", "USD", [
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax", "us-gaap:Revenues",
        "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax", "us-gaap:SalesRevenueNet"]),
    ("cost_of_revenue", "flow", "USD", ["us-gaap:CostOfRevenue", "us-gaap:CostOfGoodsAndServicesSold"]),
    ("operating_income", "flow", "USD", ["us-gaap:OperatingIncomeLoss"]),
    ("pretax_income", "flow", "USD", [
        "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"]),
    ("income_tax", "flow", "USD", ["us-gaap:IncomeTaxExpenseBenefit"]),
    ("net_income", "flow", "USD", ["us-gaap:NetIncomeLoss"]),
    ("net_income_incl_nci", "flow", "USD", ["us-gaap:ProfitLoss"]),
    ("net_income_nci", "flow", "USD", ["us-gaap:NetIncomeLossAttributableToNoncontrollingInterest"]),
    ("eps_basic", "rate", "USD/shares", ["us-gaap:EarningsPerShareBasic"]),
    ("eps_diluted", "rate", "USD/shares", ["us-gaap:EarningsPerShareDiluted"]),
    ("weighted_diluted_shares", "rate", "shares", ["us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding"]),
    ("d_and_a", "flow", "USD", [
        "us-gaap:DepreciationDepletionAndAmortization", "us-gaap:DepreciationAndAmortization",
        "us-gaap:DepreciationAmortizationAndAccretionNet"]),
    ("sbc", "flow", "USD", ["us-gaap:ShareBasedCompensation"]),
    ("cfo", "flow", "USD", ["us-gaap:NetCashProvidedByUsedInOperatingActivities"]),
    ("capex", "flow", "USD", ["us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
                              "us-gaap:PaymentsToAcquireProductiveAssets"]),
    ("cfi", "flow", "USD", ["us-gaap:NetCashProvidedByUsedInInvestingActivities"]),
    ("dividends_paid", "flow", "USD", ["us-gaap:PaymentsOfDividends", "us-gaap:PaymentsOfDividendsCommonStock"]),
    ("cff", "flow", "USD", ["us-gaap:NetCashProvidedByUsedInFinancingActivities"]),
    ("cash", "instant", "USD", ["us-gaap:CashAndCashEquivalentsAtCarryingValue"]),
    ("cash_incl_restricted", "instant", "USD", [
        "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"]),
    ("total_assets", "instant", "USD", ["us-gaap:Assets"]),
    ("total_liabilities", "instant", "USD", ["us-gaap:Liabilities"]),
    ("total_equity", "instant", "USD", ["us-gaap:StockholdersEquity"]),
    ("total_equity_incl_nci", "instant", "USD", [
        "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]),
    ("liabilities_and_equity", "instant", "USD", ["us-gaap:LiabilitiesAndStockholdersEquity"]),
    ("retained_earnings", "instant", "USD", ["us-gaap:RetainedEarningsAccumulatedDeficit"]),
    ("ppe_net", "instant", "USD", ["us-gaap:PropertyPlantAndEquipmentNet"]),
    ("long_term_debt", "instant", "USD", ["us-gaap:LongTermDebt"]),
    ("long_term_debt_noncurrent", "instant", "USD", ["us-gaap:LongTermDebtNoncurrent"]),
    ("long_term_debt_current", "instant", "USD", ["us-gaap:LongTermDebtCurrent"]),
    ("debt_current", "instant", "USD", ["us-gaap:DebtCurrent"]),
    ("short_term_borrowings", "instant", "USD", ["us-gaap:ShortTermBorrowings"]),
    ("commercial_paper", "instant", "USD", ["us-gaap:CommercialPaper"]),
    ("operating_lease_liability", "instant", "USD", ["us-gaap:OperatingLeaseLiability"]),
    ("finance_lease_liability", "instant", "USD", ["us-gaap:FinanceLeaseLiability"]),
    ("shares_outstanding_cover", "instant", "shares", ["dei:EntityCommonStockSharesOutstanding"]),
]
# Cover-page share counts are reported per class as separate facts: sum within a filing.
SUM_CLASSES_TAGS = frozenset({"dei:EntityCommonStockSharesOutstanding"})


# ---------------------------------------------------------------- units / ids
def pad_cik(cik: str | int) -> str:
    """'320193' / 'CIK0000320193' / 320193 -> '0000320193'."""
    digits = re.sub(r"\D", "", str(cik))
    if not digits:
        raise ValueError(f"not a CIK: {cik!r} (tickers must be mapped with the 'cik' command)")
    return digits.zfill(10)


def frames_unit(unit: str) -> str:
    """companyfacts unit -> frames URL unit: 'USD/shares' -> 'USD-per-shares'."""
    return unit.replace("/", "-per-")


def facts_unit(unit: str) -> str:
    """frames URL unit -> companyfacts key: 'USD-per-shares' -> 'USD/shares'."""
    return unit.replace("-per-", "/")


# ---------------------------------------------------------------- periods
def _d(s: str) -> date:
    return date.fromisoformat(s)


def period_days(fact: dict) -> int | None:
    """Days between start and end (None for an instant)."""
    if not fact.get("start"):
        return None
    return (_d(fact["end"]) - _d(fact["start"])).days


def classify(fact: dict) -> str:
    """'instant' | 'quarterly' (91 +/- 30 d) | 'annual' (365 +/- 30 d) | 'ytd' (6/9-month) | 'other'.

    Uses the data period only; `fp` is ignored because a 10-Q carries 3-month and
    year-to-date facts under the same fp."""
    days = period_days(fact)
    if days is None:
        return "instant"
    if 335 <= days <= 395:
        return "annual"
    if 61 <= days <= 121:
        return "quarterly"
    if 150 <= days <= 300:
        return "ytd"
    return "other"


def period_key(fact: dict) -> tuple[str | None, str]:
    """Dedupe key: (start, end) for durations, (None, end) for instants. Never fy/fp."""
    return (fact.get("start") or None, fact["end"])


# ---------------------------------------------------------------- loading
def load(path: str | Path) -> dict:
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))


def split_tag(tag: str, taxonomy: str | None = None) -> tuple[str, str]:
    if ":" in tag:
        tx, name = tag.split(":", 1)
        return tx, name
    return (taxonomy or "us-gaap"), tag


def concept_units(doc: dict, tag: str, taxonomy: str | None = None) -> dict[str, list[dict]] | None:
    """{unit: [facts]} for a concept, from a companyfacts or a companyconcept document."""
    tx, name = split_tag(tag, taxonomy)
    if "facts" in doc:
        node = (doc.get("facts") or {}).get(tx, {}).get(name)
        return None if node is None else node.get("units", {})
    if "units" in doc and doc.get("tag", name) == name and doc.get("taxonomy", tx) == tx:
        return doc["units"]
    return None


def facts_for(doc: dict, tag: str, taxonomy: str | None = None, unit: str | None = None) -> tuple[str, list[dict]]:
    """(unit, facts) for one concept. Refuses to guess when several unit arrays exist."""
    units = concept_units(doc, tag, taxonomy)
    if not units:
        raise KeyError(f"{split_tag(tag, taxonomy)[0]}:{split_tag(tag, taxonomy)[1]} not in this document "
                       "(it may exist only under a company extension tag or as a dimension member)")
    if unit:
        u = facts_unit(unit)
        if u not in units:
            raise KeyError(f"unit {u!r} not reported for {tag}; available: {sorted(units)}")
        return u, list(units[u])
    if len(units) > 1:
        raise ValueError(f"{tag} is reported in several units {sorted(units)}; pass --unit "
                         "(unit arrays are never summed together)")
    u = next(iter(units))
    return u, list(units[u])


def list_tags(doc: dict, grep: str | None = None) -> list[dict]:
    out = []
    for tx, concepts in (doc.get("facts") or {}).items():
        for name, node in concepts.items():
            if grep and grep.lower() not in name.lower() and grep.lower() not in (node.get("label") or "").lower():
                continue
            units = node.get("units", {})
            ends = [f["end"] for arr in units.values() for f in arr]
            out.append({"tag": f"{tx}:{name}", "label": node.get("label"),
                        "units": {u: len(a) for u, a in units.items()},
                        "first_end": min(ends) if ends else None, "last_end": max(ends) if ends else None})
    return sorted(out, key=lambda r: r["tag"])


# ---------------------------------------------------------------- dedupe
def filter_forms(facts: list[dict], forms: tuple[str, ...] | None) -> list[dict]:
    if not forms:
        return list(facts)
    allowed = {f.upper() for f in forms}
    return [f for f in facts if (f.get("form") or "").upper() in allowed]


def sum_classes(facts: list[dict]) -> list[dict]:
    """Sum per-class rows that share (accn, start, end) into one fact (cover-page share
    counts). Exact duplicate rows are counted once."""
    groups: dict[tuple, list[dict]] = {}
    for f in facts:
        groups.setdefault((f.get("accn"), f.get("start"), f["end"]), []).append(f)
    out = []
    for rows in groups.values():
        seen, uniq = set(), []
        for r in rows:
            sig = json.dumps(r, sort_keys=True)
            if sig not in seen:
                seen.add(sig)
                uniq.append(r)
        merged = dict(uniq[0])
        if len(uniq) > 1:
            merged["val"] = sum(r["val"] for r in uniq)
            merged["classes_summed"] = len(uniq)
        out.append(merged)
    return out


def dedupe(facts: list[dict], mode: str = "latest", forms: tuple[str, ...] | None = DEFAULT_FORMS,
           warnings: list[str] | None = None) -> list[dict]:
    """One fact per data period.

    mode='latest': key on period_key, keep the latest `filed` (ties: highest accn).
    mode='frame' : keep only facts carrying `frame` (calendar-aligned, last-filed)."""
    rows = filter_forms(facts, forms)
    if mode == "frame":
        rows = [f for f in rows if f.get("frame")]
    elif mode != "latest":
        raise ValueError("mode must be 'latest' or 'frame'")
    best: dict[tuple, dict] = {}
    for f in rows:
        k = period_key(f)
        cur = best.get(k)
        if cur is None:
            best[k] = f
            continue
        rank = (f.get("filed") or "", f.get("accn") or "")
        cur_rank = (cur.get("filed") or "", cur.get("accn") or "")
        if rank > cur_rank:
            best[k] = f
        elif rank == cur_rank and cur["val"] != f["val"] and warnings is not None:
            warnings.append(f"conflicting values in one filing {f.get('accn')} for period {k}: "
                            f"kept {cur['val']}, dropped {f['val']}")
    out = []
    for f in best.values():
        g = dict(f)
        g["period_type"] = classify(f)
        g["days"] = period_days(f)
        out.append(g)
    return sorted(out, key=lambda f: (f["end"], f.get("start") or ""))


def select_period(facts: list[dict], period: str) -> list[dict]:
    if period == "any":
        return facts
    return [f for f in facts if f["period_type"] == period]


# ---------------------------------------------------------------- Q4 derivation
def derive_q4(deduped: list[dict]) -> list[dict]:
    """Derived Q4 facts for a FLOW concept from deduped annual, 9-month YTD and quarterly
    facts. Skips any fiscal year that already has a quarterly fact ending on the FY end."""
    annual = [f for f in deduped if f["period_type"] == "annual"]
    quarters = [f for f in deduped if f["period_type"] == "quarterly"]
    ytd = [f for f in deduped if f["period_type"] == "ytd"]
    q_ends = {f["end"] for f in quarters}
    out = []
    for a in annual:
        if a["end"] in q_ends:
            continue
        a_start, a_end = _d(a["start"]), _d(a["end"])
        nine = [y for y in ytd if y["start"] == a["start"] and 240 <= y["days"] <= 300 and _d(y["end"]) < a_end]
        if nine:
            y = max(nine, key=lambda f: f["end"])
            out.append(_q4(a, a["val"] - y["val"], y["end"], f"FY {a['accn']} minus 9M YTD {y['accn']}"))
            continue
        inside = sorted((q for q in quarters if a_start <= _d(q["start"]) and _d(q["end"]) < a_end),
                        key=lambda q: q["end"])
        if len(inside) == 3 and inside[0]["start"] == a["start"]:
            out.append(_q4(a, a["val"] - sum(q["val"] for q in inside), inside[-1]["end"],
                           f"FY {a['accn']} minus Q1-Q3"))
    return out


def _q4(annual: dict, val: float, prior_end: str, how: str) -> dict:
    start = (_d(prior_end) + timedelta(days=1)).isoformat()
    f = {"start": start, "end": annual["end"], "val": val, "accn": annual.get("accn"),
         "filed": annual.get("filed"), "form": annual.get("form"), "fy": annual.get("fy"),
         "fp": "Q4-derived", "derived": how}
    f["period_type"] = classify(f)
    f["days"] = period_days(f)
    return f


# ---------------------------------------------------------------- series / history
def series(doc: dict, tag: str, taxonomy: str | None = None, unit: str | None = None,
           period: str = "any", mode: str = "latest", forms: tuple[str, ...] | None = DEFAULT_FORMS,
           q4: bool = False, warnings: list[str] | None = None) -> tuple[str, list[dict]]:
    u, facts = facts_for(doc, tag, taxonomy, unit)
    tx, name = split_tag(tag, taxonomy)
    if f"{tx}:{name}" in SUM_CLASSES_TAGS:
        facts = sum_classes(facts)
    rows = dedupe(facts, mode=mode, forms=forms, warnings=warnings)
    if q4:
        rows = sorted(rows + derive_q4(rows), key=lambda f: (f["end"], f.get("start") or ""))
    return u, select_period(rows, period)


def history(doc: dict, freq: str = "annual", forms: tuple[str, ...] | None = DEFAULT_FORMS,
            mode: str = "latest", warnings: list[str] | None = None) -> list[dict]:
    """Long-format 3-statement history: one row per (line item, period), with the tag used.

    annual   : annual duration facts; instants at fiscal-year ends (ends of annual facts).
    quarterly: quarterly duration facts plus derived Q4 for flow items; all instants."""
    if freq not in ("annual", "quarterly"):
        raise ValueError("freq must be annual or quarterly")
    per_item: list[tuple[str, str, str, dict[tuple, tuple[str, dict]]]] = []
    for item, kind, unit, tags in LINE_ITEMS:
        chosen: dict[tuple, tuple[str, dict]] = {}
        for tag in tags:
            try:
                _, rows = series(doc, tag, unit=unit, mode=mode, forms=forms,
                                 q4=(freq == "quarterly" and kind == "flow"), warnings=warnings)
            except KeyError:
                continue
            want = "instant" if kind == "instant" else freq
            for f in rows:
                if f["period_type"] == want:
                    chosen.setdefault(period_key(f), (tag, f))
        per_item.append((item, kind, unit, chosen))
    fy_ends = {k[1] for item, kind, _, ch in per_item if kind != "instant" for k in ch}
    if freq == "annual" and not fy_ends:
        fy_ends = None  # no annual flows found: fall back to instants from annual forms
    out = []
    for item, kind, unit, chosen in per_item:
        for (start, end), (tag, f) in sorted(chosen.items(), key=lambda kv: (kv[0][1], kv[0][0] or "")):
            if kind == "instant" and freq == "annual":
                if fy_ends is not None and end not in fy_ends:
                    continue
                if fy_ends is None and (f.get("form") or "").upper() not in ANNUAL_FORMS:
                    continue
            out.append({"line_item": item, "period_type": f["period_type"], "start": start or "",
                        "end": end, "value": f["val"], "unit": unit, "tag": tag,
                        "form": f.get("form", ""), "accn": f.get("accn", ""), "filed": f.get("filed", ""),
                        "filing_fy": f.get("fy", ""), "filing_fp": f.get("fp", ""),
                        "derived": f.get("derived", "")})
    return out


def pivot(rows: list[dict]) -> tuple[list[str], list[list]]:
    """Wide table: line items down, period ends across (annual or quarterly)."""
    ends = sorted({r["end"] for r in rows})
    order = [i for i, *_ in LINE_ITEMS]
    grid: dict[str, dict[str, float]] = {}
    for r in rows:
        grid.setdefault(r["line_item"], {})[r["end"]] = r["value"]
    header = ["line_item"] + ends
    body = [[item] + [grid[item].get(e, "") for e in ends] for item in order if item in grid]
    return header, body


# ---------------------------------------------------------------- network
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
WRAPPER = "edgar_facts"
APPROVED_HOSTS = frozenset({"data.sec.gov", "www.sec.gov"})
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


class Throttle:
    """Minimum spacing between requests (token bucket of size 1)."""

    def __init__(self, per_second: float = MAX_REQ_PER_SEC):
        self.interval = 1.0 / per_second
        self._last = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        delay = self._last + self.interval - now
        if delay > 0:
            time.sleep(delay)
        self._last = time.monotonic()


class SharedThrottle:
    """The same spacing, held across processes: SEC's 10/s ceiling is per client, and the
    agent runs this script once per fetch, often several at a time, so an in-process
    timer never sees the other calls. The last request's wall-clock time lives in a
    stamp file guarded by flock. Without fcntl, or on any OS error opening, locking or
    writing the stamp file, it falls back to Throttle: a throttle problem must never abort the fetch itself."""

    def __init__(self, path: str | Path | None = None, per_second: float = MAX_REQ_PER_SEC):
        self.interval = 1.0 / per_second
        self.path = Path(path or os.environ.get(THROTTLE_FILE_ENV) or default_throttle_path())
        self._local = Throttle(per_second)

    def wait(self) -> float | None:
        """Wait for this request's slot; return the stamp written, or None on the fallback."""
        try:
            import fcntl
        except ImportError:
            return self._local.wait()
        try:
            with open(self.path, "a+") as fh:
                fcntl.flock(fh, fcntl.LOCK_EX)
                try:
                    fh.seek(0)
                    try:
                        last = float(fh.read().strip() or 0)
                    except ValueError:
                        last = 0.0
                    delay = last + self.interval - time.time()
                    if delay > 0:
                        time.sleep(min(delay, self.interval))
                    now = time.time()
                    fh.seek(0)
                    fh.truncate()
                    fh.write(repr(now))
                    fh.flush()
                    return now
                finally:
                    fcntl.flock(fh, fcntl.LOCK_UN)
        except OSError:
            # open, flock (ENOLCK on a network mount) or the write (ENOSPC): degrade, never
            # abort. A stamp left empty by a failed write reads as 0, which is harmless.
            return self._local.wait()


def default_throttle_path() -> Path:
    """Shared storage when the runner provides it, so every agent on the computer (one
    SEC client IP) shares the stamp even when a harness overrides TMPDIR per process;
    else a per-user file in the temp dir, so another OS user's stamp can't lock us out."""
    shared = os.environ.get("AGENT_SHARED_STORAGE_DIR", "").strip()
    if shared and Path(shared).is_dir():
        return Path(shared) / "edgar-throttle"
    uid = os.getuid() if hasattr(os, "getuid") else "user"
    return Path(tempfile.gettempdir()) / f"manigent-edgar-throttle-{uid}"


_THROTTLE = SharedThrottle()


def user_agent(explicit: str | None) -> str:
    ua = (explicit or os.environ.get(UA_ENV, "")).strip()
    if not re.search(r"[^@\s]+@[^@\s]+\.[^@\s]+", ua):
        sys.exit(f"SEC requires a User-Agent with a contact e-mail: pass --user-agent "
                 f"\"Org Name contact@domain\" or set ${UA_ENV}.")
    return ua


def http_get(url: str, ua: str) -> bytes:
    if web_disabled():
        sys.exit(f"{WEB_DISABLED_ENV}={os.environ[WEB_DISABLED_ENV].strip()}: web access is off for this "
                 "run, so SEC EDGAR is not called. Work offline on a saved JSON with "
                 "'series' / 'history' / 'tags' instead.")
    _THROTTLE.wait()
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "gzip, deflate",
                                               "Accept": "application/json"})
    try:
        with net_open(req, timeout=60) as resp:
            body = resp.read()
            enc = (resp.headers.get("Content-Encoding") or "").lower()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"SEC 404 for {url} (unknown CIK/tag/unit/period, or no facts)")
        if e.code in (403, 429):
            sys.exit(f"SEC HTTP {e.code} for {url}: throttled or User-Agent rejected; slow down and "
                     "check the contact e-mail")
        sys.exit(f"SEC HTTP {e.code} for {url}")
    except urllib.error.URLError as e:
        sys.exit(f"SEC unreachable ({e.reason})")
    if enc == "gzip":
        body = gzip.decompress(body)
    elif enc == "deflate":
        body = zlib.decompress(body)
    return body


def fetch_url(kind: str, args) -> str:
    if kind == "companyfacts":
        return f"{DATA_SEC}/api/xbrl/companyfacts/CIK{pad_cik(args.cik)}.json"
    if kind == "concept":
        tx, name = split_tag(args.tag, args.taxonomy)
        return f"{DATA_SEC}/api/xbrl/companyconcept/CIK{pad_cik(args.cik)}/{tx}/{name}.json"
    if kind == "frames":
        tx, name = split_tag(args.tag, args.taxonomy)
        if not re.fullmatch(r"CY\d{4}(Q[1-4]I?)?", args.period or ""):
            sys.exit("--period must be CY####, CY####Q# or CY####Q#I (I = instant, for balance-sheet items)")
        return f"{DATA_SEC}/api/xbrl/frames/{tx}/{name}/{frames_unit(args.unit)}/{args.period}.json"
    if kind == "submissions":
        return f"{DATA_SEC}/submissions/CIK{pad_cik(args.cik)}.json"
    raise ValueError(kind)


def ticker_to_cik(ticker: str, doc: dict) -> list[dict]:
    t = ticker.strip().upper()
    rows = doc.values() if isinstance(doc, dict) else doc
    return [{"ticker": r["ticker"], "cik": pad_cik(r["cik_str"]), "title": r.get("title")}
            for r in rows if str(r.get("ticker", "")).upper() == t]


# ---------------------------------------------------------------- CLI
def _write(rows: list[dict] | tuple, fmt: str, out: str | None) -> None:
    buf = io.StringIO()
    if fmt == "json":
        json.dump(rows if not isinstance(rows, tuple) else {"header": rows[0], "rows": rows[1]}, buf, indent=1)
        buf.write("\n")
    else:
        w = csv.writer(buf, lineterminator="\n")
        if isinstance(rows, tuple):
            w.writerow(rows[0])
            w.writerows(rows[1])
        elif rows:
            cols = list(rows[0].keys())
            w.writerow(cols)
            for r in rows:
                w.writerow([r.get(c, "") for c in cols])
    if out:
        Path(out).write_text(buf.getvalue(), encoding="utf-8")
        print(f"wrote {out}", file=sys.stderr)
    else:
        sys.stdout.write(buf.getvalue())


def _forms(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return DEFAULT_FORMS
    if value.strip().lower() == "all":
        return None
    return tuple(v.strip() for v in value.split(",") if v.strip())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("tags", help="list concepts in a companyfacts JSON")
    t.add_argument("--facts", required=True)
    t.add_argument("--grep")

    s = sub.add_parser("series", help="deduped time series for one concept")
    s.add_argument("--facts", required=True)
    s.add_argument("--tag", required=True)
    s.add_argument("--taxonomy")
    s.add_argument("--unit")
    s.add_argument("--period", default="any", choices=PERIOD_TYPES + ("any",))
    s.add_argument("--mode", default="latest", choices=("latest", "frame"))
    s.add_argument("--forms", help="comma list, or 'all' (default: 10-K/10-Q/20-F/40-F and amendments)")
    s.add_argument("--derive-q4", action="store_true", help="add derived Q4 rows (flow items only)")
    s.add_argument("--format", default="csv", choices=("csv", "json"))
    s.add_argument("--out")

    h = sub.add_parser("history", help="normalised 3-statement history")
    h.add_argument("--facts", required=True)
    h.add_argument("--freq", default="annual", choices=("annual", "quarterly"))
    h.add_argument("--mode", default="latest", choices=("latest", "frame"))
    h.add_argument("--forms")
    h.add_argument("--wide", action="store_true")
    h.add_argument("--format", default="csv", choices=("csv", "json"))
    h.add_argument("--out")

    f = sub.add_parser("fetch", help="download from SEC (network)")
    f.add_argument("kind", choices=("companyfacts", "concept", "frames", "submissions"))
    f.add_argument("--cik")
    f.add_argument("--tag")
    f.add_argument("--taxonomy")
    f.add_argument("--unit", default="USD")
    f.add_argument("--period")
    f.add_argument("--user-agent")
    f.add_argument("--out")

    c = sub.add_parser("cik", help="map a ticker to a 10-digit CIK")
    c.add_argument("--ticker", required=True)
    c.add_argument("--tickers-file", help="saved company_tickers.json (offline)")
    c.add_argument("--user-agent")

    args = p.parse_args(argv)
    net_start(args.cmd)
    warnings: list[str] = []

    if args.cmd == "tags":
        print(json.dumps(list_tags(load(args.facts), args.grep), indent=1))
    elif args.cmd == "series":
        unit, rows = series(load(args.facts), args.tag, args.taxonomy, args.unit, args.period,
                            args.mode, _forms(args.forms), args.derive_q4, warnings)
        cols = ("start", "end", "days", "period_type", "val", "form", "accn", "filed", "fy", "fp", "frame", "derived")
        _write([{**{k: r.get(k, "") for k in cols}, "unit": unit} for r in rows], args.format, args.out)
    elif args.cmd == "history":
        rows = history(load(args.facts), args.freq, _forms(args.forms), args.mode, warnings)
        _write(pivot(rows) if args.wide else rows, args.format, args.out)
    elif args.cmd == "fetch":
        if args.kind in ("companyfacts", "concept", "submissions") and not args.cik:
            sys.exit("--cik is required")
        if args.kind in ("concept", "frames") and not args.tag:
            sys.exit("--tag is required")
        url = fetch_url(args.kind, args)
        body = http_get(url, user_agent(args.user_agent))
        if args.out:
            Path(args.out).write_bytes(body)
            print(f"wrote {args.out} ({len(body)} bytes) from {url}", file=sys.stderr)
        else:
            sys.stdout.write(body.decode("utf-8"))
    elif args.cmd == "cik":
        if args.tickers_file:
            doc = load(args.tickers_file)
        else:
            doc = json.loads(http_get(TICKERS_URL, user_agent(args.user_agent)).decode("utf-8"))
        hits = ticker_to_cik(args.ticker, doc)
        print(json.dumps(hits, indent=1))
        if not hits:
            print("no match", file=sys.stderr)
            return 1
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
