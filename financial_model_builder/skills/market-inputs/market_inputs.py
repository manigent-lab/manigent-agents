#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Manigent Contributors
"""Point-in-time discount-rate inputs, each stamped with its source and the date inside the data.

    python market_inputs.py treasury --as-of 2026-09-30 [--tenor 10y] [--csv saved.csv]
    python market_inputs.py erp      --as-of 2026-09-30 [--variant headline] [--xlsx ERPbymonth.xlsx]
    python market_inputs.py wacc-inputs --as-of 2026-09-30 [--tenor 10y] [--variant headline]

Every answer is JSON with `value` (a decimal, 0.0524 = 5.24%), `as_of` (the date the value
is FOR, read from the data itself), `requested_as_of`, `series`, `source_url` and, for
downloaded files, `last_modified` (when the file changed, which is NOT the data date).

Rules applied:
  * Point in time. --as-of picks the last observation ON OR BEFORE that date: the Treasury
    row for that day (or the prior business day), the Damodaran month whose start is on or
    before it. A 2026-09-30 valuation gets the September ERP, never October's.
  * Named variant. Damodaran publishes several ERPs per month; the answer always carries
    which column it came from. "headline" is his T12m-with-sustainable-payout figure.
  * Same series. wacc-inputs also reports the riskfree rate Damodaran used for that month
    and warns when it differs from the Treasury observation by more than 25 bp.
  * ERPbymonth.xlsx uses the 1904 date system; dates are converted by the workbook's own
    flag, not assumed.

Online fetches are refused when MANIGENT_WEB_DISABLED is 1 / true / yes; pass a saved file
with --csv / --xlsx instead. Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

WEB_DISABLED_ENV = "MANIGENT_WEB_DISABLED"
UA = "Manigent financial_model_builder (market-inputs skill)"

TREASURY_URL = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
                "daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve"
                "&field_tdr_date_value={year}&_format=csv")
TREASURY_SERIES = "US Treasury Daily Par Yield Curve Rates"
TENORS = {"1m": "1 Mo", "2m": "2 Mo", "3m": "3 Mo", "4m": "4 Mo", "6m": "6 Mo", "1y": "1 Yr",
          "2y": "2 Yr", "3y": "3 Yr", "5y": "5 Yr", "7y": "7 Yr", "10y": "10 Yr", "20y": "20 Yr",
          "30y": "30 Yr"}

ERP_URL = "https://pages.stern.nyu.edu/~adamodar/pc/implprem/ERPbymonth.xlsx"
ERP_SHEET = "Historical ERP"
# CLI name -> column header in the "Historical ERP" sheet.
ERP_VARIANTS = {
    "headline": "ERP (T12 m with sustainable payout)",
    "t12m": "ERP (T12m)",
    "t12m-adj-riskfree": "ERP (T12m) with adj riskfree rate",
    "smoothed": "ERP (Smoothed)",
    "normalized": "ERP (Normalized)",
    "net-cash-yield": "ERP (Net Cash Yield)",
}
ERP_RISKFREE_COL = "T.Bond Rate"
ERP_MONTH_COL = "Start of month"
SAME_SERIES_TOLERANCE = 0.0025

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "rel": "http://schemas.openxmlformats.org/package/2006/relationships"}


class InputError(Exception):
    """No observation fits the request (bad tenor, as-of before the data starts, ...)."""


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
WRAPPER = "market_inputs"
APPROVED_HOSTS = frozenset({"home.treasury.gov", "pages.stern.nyu.edu"})
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


def http_get(url: str) -> tuple[bytes, str]:
    """GET url; returns (body, Last-Modified as YYYY-MM-DD or "")."""
    if web_disabled():
        sys.exit(f"{WEB_DISABLED_ENV} is set: web access is off for this run. Pass a saved file "
                 "(--csv / --xlsx) or say the input is as of your snapshot date.")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with net_open(req, timeout=60) as resp:
            body = resp.read()
            lm = resp.headers.get("Last-Modified") or ""
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} for {url}")
    except urllib.error.URLError as e:
        sys.exit(f"unreachable: {url} ({e.reason})")
    return body, _http_date(lm)


def _http_date(value: str) -> str:
    try:
        return parsedate_to_datetime(value).date().isoformat() if value else ""
    except (TypeError, ValueError):
        return ""


# ---------------------------------------------------------------- Treasury par curve

def parse_treasury_csv(text: str) -> list[dict]:
    """Rows of the Treasury CSV as {"date": date, <column header>: float|None}."""
    rows = []
    for raw in csv.DictReader(io.StringIO(text)):
        d = datetime.strptime(raw["Date"].strip(), "%m/%d/%Y").date()
        row: dict = {"date": d}
        for k, v in raw.items():
            if k != "Date":
                v = (v or "").strip()
                row[k.strip()] = float(v) if v else None
        rows.append(row)
    return rows


def treasury_obs(rows: list[dict], as_of: date, tenor: str) -> dict:
    """The last observation on or before as_of that has a value for tenor."""
    col = TENORS.get(tenor.lower())
    if col is None:
        raise InputError(f"unknown tenor {tenor!r}; use one of {', '.join(TENORS)}")
    best = None
    for r in rows:
        if r["date"] <= as_of and r.get(col) is not None and (best is None or r["date"] > best["date"]):
            best = r
    if best is None:
        raise InputError(f"no {col} observation on or before {as_of}")
    return {"value": round(best[col] / 100, 6), "as_of": best["date"].isoformat(),
            "requested_as_of": as_of.isoformat(), "series": f"{TREASURY_SERIES}, {col} par yield",
            "tenor": tenor.lower()}


def treasury(as_of: date, tenor: str = "10y", csv_path: str | None = None) -> dict:
    if csv_path:
        obs = treasury_obs(parse_treasury_csv(Path(csv_path).read_text(encoding="utf-8-sig")), as_of, tenor)
        obs.update(source_url=f"file:{csv_path}", last_modified="")
        return obs
    # The CSV is per calendar year; an as-of in the first days of January may need last year.
    for year in (as_of.year, as_of.year - 1):
        url = TREASURY_URL.format(year=year)
        body, lm = http_get(url)
        try:
            obs = treasury_obs(parse_treasury_csv(body.decode("utf-8-sig")), as_of, tenor)
        except InputError:
            continue
        obs.update(source_url=url, last_modified=lm)
        return obs
    raise InputError(f"no Treasury {tenor} observation on or before {as_of}")


# ---------------------------------------------------------------- Damodaran ERP

def _sheet_rows(xlsx: bytes, sheet_name: str) -> tuple[list[list], bool]:
    """Cell values of one worksheet as rows (strings or floats), plus the date1904 flag."""
    z = zipfile.ZipFile(io.BytesIO(xlsx))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    pr = wb.find("m:workbookPr", NS)
    date1904 = pr is not None and pr.get("date1904") in ("1", "true")
    rid = None
    for s in wb.iterfind("m:sheets/m:sheet", NS):
        if s.get("name") == sheet_name:
            rid = s.get(f"{{{NS['r']}}}id")
    if rid is None:
        raise InputError(f"sheet {sheet_name!r} not found; the workbook layout changed")
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = next((r.get("Target") for r in rels.iterfind("rel:Relationship", NS) if r.get("Id") == rid), None)
    if target is None:
        raise InputError(f"sheet {sheet_name!r} has no part in the workbook rels; the workbook layout changed")
    path = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
    shared: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iterfind("m:si", NS):
            shared.append(_rich_text(si))
    rows = []
    for row in ET.fromstring(z.read(path)).iterfind("m:sheetData/m:row", NS):
        out: list = []
        for c in row.iterfind("m:c", NS):
            ref = c.get("r")
            col = _col_index(ref) if ref else len(out)
            while len(out) < col:
                out.append(None)
            v = c.find("m:v", NS)
            if c.get("t") == "inlineStr":
                is_ = c.find("m:is", NS)
                val = _rich_text(is_) if is_ is not None else ""
            elif v is None or v.text is None:
                val = None
            elif c.get("t") == "s":
                val = shared[int(v.text)]
            elif c.get("t") in ("str", "e", "d"):
                val = v.text
            else:
                val = float(v.text)
            out.append(val)
        rows.append(out)
    return rows, date1904


def _rich_text(el: ET.Element) -> str:
    """Text of a string item: its direct <t> or its <r><t> runs. Phonetic <rPh> runs are skipped."""
    t = el.find("m:t", NS)
    if t is not None:
        return t.text or ""
    return "".join(r.findtext("m:t", "", NS) for r in el.iterfind("m:r", NS))


def _col_index(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def excel_date(serial: float, date1904: bool) -> date:
    base = date(1904, 1, 1) if date1904 else date(1899, 12, 30)
    return base + timedelta(days=int(serial))


def erp_obs(xlsx: bytes, as_of: date, variant: str = "headline") -> dict:
    header_name = ERP_VARIANTS.get(variant)
    if header_name is None:
        raise InputError(f"unknown variant {variant!r}; use one of {', '.join(ERP_VARIANTS)}")
    rows, date1904 = _sheet_rows(xlsx, ERP_SHEET)
    header = [str(h).strip() if h is not None else "" for h in rows[0]]
    try:
        i_month, i_erp, i_rf = (header.index(ERP_MONTH_COL), header.index(header_name),
                                header.index(ERP_RISKFREE_COL))
    except ValueError as e:
        raise InputError(f"column missing from {ERP_SHEET!r}: {e}; the workbook layout changed")
    best = None
    for r in rows[1:]:
        cell = lambda i: r[i] if i < len(r) else None  # noqa: E731
        if not isinstance(cell(i_month), float) or not isinstance(cell(i_erp), float):
            continue
        month = excel_date(cell(i_month), date1904)
        if month <= as_of and (best is None or month > best[0]):
            best = (month, cell(i_erp), cell(i_rf))
    if best is None:
        raise InputError(f"no {header_name} value for a month starting on or before {as_of}")
    month, erp, rf = best
    return {"value": round(erp, 6), "as_of": month.isoformat(), "requested_as_of": as_of.isoformat(),
            "series": f"Damodaran implied ERP, {header_name}", "variant": variant,
            "riskfree_used": round(rf, 6) if isinstance(rf, float) else None,
            "riskfree_series": f"Damodaran {ERP_RISKFREE_COL} (10y Treasury at start of month)"}


def erp(as_of: date, variant: str = "headline", xlsx_path: str | None = None) -> dict:
    if xlsx_path:
        obs = erp_obs(Path(xlsx_path).read_bytes(), as_of, variant)
        obs.update(source_url=f"file:{xlsx_path}", last_modified="")
        return obs
    body, lm = http_get(ERP_URL)
    obs = erp_obs(body, as_of, variant)
    obs.update(source_url=ERP_URL, last_modified=lm)
    return obs


def wacc_inputs(as_of: date, tenor: str = "10y", variant: str = "headline",
                csv_path: str | None = None, xlsx_path: str | None = None) -> dict:
    rf = treasury(as_of, tenor, csv_path)
    prem = erp(as_of, variant, xlsx_path)
    warnings = []
    # Damodaran's riskfree is the 10y, so the check only means something against the 10y.
    if rf["tenor"] == "10y" and prem["riskfree_used"] is not None and abs(prem["riskfree_used"] - rf["value"]) > SAME_SERIES_TOLERANCE:
        warnings.append(
            f"Damodaran's {prem['as_of']} ERP was computed against a {prem['riskfree_used']:.2%} riskfree "
            f"rate; the Treasury {rf['tenor']} on {rf['as_of']} is {rf['value']:.2%}. Pair the ERP with "
            "its own riskfree rate, or say why you mix them.")
    return {"riskfree": rf, "erp": prem, "warnings": warnings}


def _date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("treasury", help="par yield for a tenor, last observation on or before --as-of")
    t.add_argument("--tenor", default="10y")
    t.add_argument("--csv", help="saved Treasury CSV (offline)")
    e = sub.add_parser("erp", help="Damodaran implied ERP for the month starting on or before --as-of")
    e.add_argument("--variant", default="headline", choices=sorted(ERP_VARIANTS))
    e.add_argument("--xlsx", help="saved ERPbymonth.xlsx (offline)")
    w = sub.add_parser("wacc-inputs", help="riskfree + ERP for one as-of date, with a same-series check")
    w.add_argument("--tenor", default="10y")
    w.add_argument("--variant", default="headline", choices=sorted(ERP_VARIANTS))
    w.add_argument("--csv")
    w.add_argument("--xlsx")
    for s in (t, e, w):
        s.add_argument("--as-of", type=_date, default=date.today(), help="YYYY-MM-DD (default today)")
    a = p.parse_args(argv)
    net_start(a.cmd)
    try:
        if a.cmd == "treasury":
            out = treasury(a.as_of, a.tenor, a.csv)
        elif a.cmd == "erp":
            out = erp(a.as_of, a.variant, a.xlsx)
        else:
            out = wacc_inputs(a.as_of, a.tenor, a.variant, a.csv, a.xlsx)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
