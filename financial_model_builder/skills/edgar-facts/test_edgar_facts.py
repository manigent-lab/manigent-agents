# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Manigent Contributors
"""Unit tests for edgar_facts.py on a synthetic companyfacts document (no network).

Run: python3 -m pytest test_edgar_facts.py   (or python3 -m unittest test_edgar_facts)
The filer, CIK, tags' values and accession numbers below are invented.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edgar_facts as ef  # noqa: E402


def fact(val, end, start=None, accn="A", fy=2025, fp="FY", form="10-K", filed="2025-11-01", frame=None):
    f = {"end": end, "val": val, "accn": accn, "fy": fy, "fp": fp, "form": form, "filed": filed}
    if start:
        f["start"] = start
    if frame:
        f["frame"] = frame
    return f


# Synthetic filer with a 52/53-week fiscal year ending late September.
FY23 = ("2022-10-02", "2023-09-30")
FY24 = ("2023-10-01", "2024-09-28")
FY25 = ("2024-09-29", "2025-09-27")
K23 = dict(accn="K23", fy=2023, filed="2023-11-03")
K24 = dict(accn="K24", fy=2024, filed="2024-11-01")
K25 = dict(accn="K25", fy=2025, filed="2025-10-31")
Q1 = dict(accn="Q1-25", fy=2025, fp="Q1", form="10-Q", filed="2025-01-31")
Q2 = dict(accn="Q2-25", fy=2025, fp="Q2", form="10-Q", filed="2025-05-02")
Q3 = dict(accn="Q3-25", fy=2025, fp="Q3", form="10-Q", filed="2025-08-01")


def synthetic_doc():
    rev_new = [
        # FY2023 appears in three 10-Ks (fy 2023, 2024, 2025); only the last-filed has frame.
        fact(900, FY23[1], FY23[0], **K23),
        fact(900, FY23[1], FY23[0], **K24),
        fact(900, FY23[1], FY23[0], frame="CY2023", **K25),
        fact(1000, FY24[1], FY24[0], **K24),
        fact(1010, FY24[1], FY24[0], frame="CY2024", **K25),  # recast in the later 10-K
        fact(1100, FY25[1], FY25[0], frame="CY2025", **K25),
        fact(250, "2024-12-28", "2024-09-29", frame="CY2024Q4", **Q1),
        fact(260, "2025-03-29", "2024-12-29", frame="CY2025Q1", **Q2),
        fact(510, "2025-03-29", "2024-09-29", **Q2),               # 6-month YTD, same fp
        fact(270, "2025-06-28", "2025-03-30", frame="CY2025Q2", **Q3),
        fact(780, "2025-06-28", "2024-09-29", **Q3),               # 9-month YTD
        fact(5, "2025-06-28", "2025-03-30", accn="8K", form="8-K", filed="2025-08-02"),
    ]
    rev_old = [
        fact(700, "2021-09-25", "2020-09-27", **K23),
        fact(880, FY23[1], FY23[0], **K23),  # overlap with the newer tag: newer tag wins
    ]
    assets = [
        fact(5000, FY24[1], **K24), fact(5000, FY24[1], **K25),
        fact(5600, FY25[1], frame="CY2025Q3I", **K25),
        fact(5400, "2025-06-28", **Q3),
    ]
    ni = [fact(100, FY24[1], FY24[0], **K25), fact(120, FY25[1], FY25[0], **K25),
          fact(30, "2024-12-28", "2024-09-29", **Q1), fact(31, "2025-03-29", "2024-12-29", **Q2),
          fact(32, "2025-06-28", "2025-03-30", **Q3)]
    eps = [fact(1.2, FY25[1], FY25[0], **K25), fact(1.0, FY24[1], FY24[0], **K25)]
    shares_cover = [fact(600, "2025-10-20", **K25), fact(300, "2025-10-20", **K25)]  # two classes
    return {
        "cik": 1, "entityName": "Synthetic Widgets Inc.",
        "facts": {
            "dei": {"EntityCommonStockSharesOutstanding": {"label": "Shares", "units": {"shares": shares_cover}}},
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {"label": "Revenue", "units": {"USD": rev_new}},
                "SalesRevenueNet": {"label": "Sales", "units": {"USD": rev_old}},
                "Assets": {"label": "Assets", "units": {"USD": assets}},
                "NetIncomeLoss": {"label": "NI", "units": {"USD": ni}},
                "EarningsPerShareDiluted": {"label": "EPS", "units": {"USD/shares": eps}},
                "MixedUnits": {"label": "x", "units": {"USD": [fact(1, FY25[1], FY25[0])],
                                                       "EUR": [fact(2, FY25[1], FY25[0])]}},
            },
        },
    }


REV = "RevenueFromContractWithCustomerExcludingAssessedTax"


class Ids(unittest.TestCase):
    def test_pad_cik(self):
        self.assertEqual(ef.pad_cik(320), "0000000320")
        self.assertEqual(ef.pad_cik("CIK0000000320"), "0000000320")
        with self.assertRaises(ValueError):
            ef.pad_cik("ABCD")

    def test_units_round_trip(self):
        self.assertEqual(ef.frames_unit("USD/shares"), "USD-per-shares")
        self.assertEqual(ef.facts_unit("USD-per-shares"), "USD/shares")
        self.assertEqual(ef.frames_unit("USD"), "USD")


class Periods(unittest.TestCase):
    def test_classify_by_length_not_fp(self):
        self.assertEqual(ef.classify(fact(1, FY25[1], FY25[0])), "annual")
        self.assertEqual(ef.classify(fact(1, "2025-03-29", "2024-12-29", fp="Q2")), "quarterly")
        self.assertEqual(ef.classify(fact(1, "2025-03-29", "2024-09-29", fp="Q2")), "ytd")
        self.assertEqual(ef.classify(fact(1, "2025-03-29")), "instant")


class Dedupe(unittest.TestCase):
    def setUp(self):
        self.doc = synthetic_doc()

    def test_one_row_per_period_and_latest_filed_wins(self):
        _, rows = ef.series(self.doc, REV, period="annual")
        self.assertEqual([r["end"] for r in rows], [FY23[1], FY24[1], FY25[1]])
        fy24 = next(r for r in rows if r["end"] == FY24[1])
        self.assertEqual(fy24["val"], 1010)          # recast value from the later filing
        self.assertEqual(fy24["accn"], "K25")

    def test_frame_mode_keeps_only_framed_rows(self):
        _, rows = ef.series(self.doc, REV, mode="frame")
        self.assertTrue(all(r.get("frame") for r in rows))
        self.assertEqual(len([r for r in rows if r["end"] == FY23[1]]), 1)

    def test_forms_filter_drops_8k(self):
        _, rows = ef.series(self.doc, REV, period="quarterly")
        self.assertNotIn("8K", {r["accn"] for r in rows})
        _, rows_all = ef.series(self.doc, REV, period="quarterly", forms=None)
        self.assertIn("8K", {r["accn"] for r in rows_all})

    def test_same_fp_three_month_and_ytd_kept_apart(self):
        _, rows = ef.series(self.doc, REV)
        q2 = [r for r in rows if r["end"] == "2025-03-29"]
        self.assertEqual(sorted(r["period_type"] for r in q2), ["quarterly", "ytd"])

    def test_conflict_in_one_filing_is_warned(self):
        facts = [fact(1, FY25[1], FY25[0], accn="X"), fact(2, FY25[1], FY25[0], accn="X")]
        warnings = []
        ef.dedupe(facts, warnings=warnings)
        self.assertEqual(len(warnings), 1)

    def test_multiple_units_refused_without_unit(self):
        with self.assertRaises(ValueError):
            ef.series(self.doc, "MixedUnits")
        unit, rows = ef.series(self.doc, "MixedUnits", unit="EUR")
        self.assertEqual((unit, rows[0]["val"]), ("EUR", 2))

    def test_frames_style_unit_accepted(self):
        unit, rows = ef.series(self.doc, "EarningsPerShareDiluted", unit="USD-per-shares")
        self.assertEqual(unit, "USD/shares")
        self.assertEqual(len(rows), 2)

    def test_missing_tag_mentions_extensions(self):
        with self.assertRaises(KeyError) as cm:
            ef.series(self.doc, "OperatingIncomeLoss")
        self.assertIn("extension", str(cm.exception))

    def test_cover_page_classes_summed(self):
        _, rows = ef.series(self.doc, "dei:EntityCommonStockSharesOutstanding")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["val"], 900)


class Q4(unittest.TestCase):
    def test_q4_from_nine_month_ytd(self):
        _, rows = ef.series(synthetic_doc(), REV, period="quarterly", q4=True)
        q4 = [r for r in rows if r.get("derived")]
        self.assertEqual(len(q4), 1)
        self.assertEqual(q4[0]["val"], 1100 - 780)
        self.assertEqual((q4[0]["start"], q4[0]["end"]), ("2025-06-29", FY25[1]))
        self.assertEqual(q4[0]["period_type"], "quarterly")

    def test_q4_from_three_quarters_when_no_ytd(self):
        _, rows = ef.series(synthetic_doc(), "NetIncomeLoss", period="quarterly", q4=True)
        q4 = [r for r in rows if r.get("derived")]
        self.assertEqual([r["val"] for r in q4], [120 - (30 + 31 + 32)])


class History(unittest.TestCase):
    def test_annual_history_stitches_tags_and_keeps_fy_end_instants(self):
        rows = ef.history(synthetic_doc(), "annual")
        rev = {r["end"]: r for r in rows if r["line_item"] == "revenue"}
        self.assertEqual(rev[FY23[1]]["tag"], "us-gaap:" + REV)        # newer tag preferred
        self.assertEqual(rev["2021-09-25"]["tag"], "us-gaap:SalesRevenueNet")
        assets = {r["end"] for r in rows if r["line_item"] == "total_assets"}
        self.assertEqual(assets, {FY24[1], FY25[1]})                   # 10-Q instant excluded
        self.assertNotIn("operating_income", {r["line_item"] for r in rows})  # never imputed

    def test_tag_switch_falls_through_per_period(self):
        # Filers that stop using the ASC 606 tag (Alphabet reports FY2025 revenue only under
        # Revenues) must still get FY2025 revenue, from the next tag in the fallback list.
        doc = synthetic_doc()
        gaap = doc["facts"]["us-gaap"]
        gaap[REV]["units"]["USD"] = [f for f in gaap[REV]["units"]["USD"] if f["end"] != FY25[1]]
        gaap["Revenues"] = {"label": "Revenues", "units": {"USD": [fact(1150, FY25[1], FY25[0], **K25)]}}
        rev = {r["end"]: r for r in ef.history(doc, "annual") if r["line_item"] == "revenue"}
        self.assertEqual((rev[FY25[1]]["tag"], rev[FY25[1]]["value"]), ("us-gaap:Revenues", 1150))
        self.assertEqual(rev[FY24[1]]["tag"], "us-gaap:" + REV)

    def test_quarterly_history_has_derived_q4_and_filing_labels(self):
        rows = ef.history(synthetic_doc(), "quarterly")
        rev = [r for r in rows if r["line_item"] == "revenue"]
        self.assertTrue(any(r["derived"] for r in rev))
        self.assertTrue(all("filing_fy" in r for r in rev))

    def test_wide_pivot(self):
        header, body = ef.pivot(ef.history(synthetic_doc(), "annual"))
        self.assertEqual(header[0], "line_item")
        self.assertEqual(body[0][0], "revenue")

    def test_cli_offline_on_saved_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "cf.json"
            p.write_text(json.dumps(synthetic_doc()))
            out = Path(d) / "h.csv"
            self.assertEqual(ef.main(["history", "--facts", str(p), "--out", str(out)]), 0)
            self.assertIn("revenue", out.read_text())


class Network(unittest.TestCase):
    def test_web_disabled_refuses_before_any_request(self):
        with mock.patch.dict(os.environ, {"MANIGENT_WEB_DISABLED": "1"}), \
                mock.patch("urllib.request.urlopen") as op:
            with self.assertRaises(SystemExit):
                ef.http_get("https://data.sec.gov/x", "Org ops@example.com")
            op.assert_not_called()

    def test_user_agent_needs_email(self):
        with mock.patch.dict(os.environ, {"SEC_USER_AGENT": ""}):
            with self.assertRaises(SystemExit):
                ef.user_agent("Just A Name")
        self.assertEqual(ef.user_agent("Org ops@example.com"), "Org ops@example.com")

    def test_request_headers_and_rate(self):
        self.assertLess(ef.MAX_REQ_PER_SEC, 10)
        seen = {}

        class Resp:
            headers = {}

            def read(self):
                return b"{}"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_open(req, timeout):
            seen.update(dict(req.header_items()))
            return Resp()

        with tempfile.TemporaryDirectory() as d, \
                mock.patch.dict(os.environ, {"MANIGENT_WEB_DISABLED": ""}), \
                mock.patch.object(ef, "_THROTTLE", ef.SharedThrottle(os.path.join(d, "stamp"))), \
                mock.patch("urllib.request.urlopen", fake_open):
            ef.http_get("https://data.sec.gov/x", "Org ops@example.com")
        self.assertEqual(seen.get("User-agent"), "Org ops@example.com")
        self.assertEqual(seen.get("Accept-encoding"), "gzip, deflate")

    def test_throttle_spacing(self):
        t = ef.Throttle(per_second=8)
        with mock.patch("time.sleep") as sl, mock.patch("time.monotonic", side_effect=[100.0, 100.0, 100.01, 100.125]):
            t.wait()
            t.wait()
        sl.assert_called_once()
        self.assertAlmostEqual(sl.call_args[0][0], 0.115, places=6)

    def test_shared_throttle_spaces_calls_across_processes(self):
        import subprocess
        import tempfile as tf
        with tf.TemporaryDirectory() as d:
            stamp = os.path.join(d, "stamp")
            code = ("import sys, time; sys.path.insert(0, %r); import edgar_facts as ef; "
                    "print(ef.SharedThrottle(%r, per_second=4).wait())"
                    % (os.path.dirname(os.path.abspath(ef.__file__)), stamp))
            procs = [subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
                     for _ in range(4)]
            stamps = sorted(float(p.communicate()[0]) for p in procs)
        gaps = [b - a for a, b in zip(stamps, stamps[1:])]
        self.assertTrue(all(g >= 0.249 for g in gaps), gaps)

    def test_shared_throttle_tolerates_garbage_stamp(self):
        import tempfile as tf
        with tf.TemporaryDirectory() as d:
            stamp = os.path.join(d, "stamp")
            with open(stamp, "w") as fh:
                fh.write("not a number")
            with mock.patch("time.sleep") as sl:
                ef.SharedThrottle(stamp).wait()
            sl.assert_not_called()

    def test_shared_throttle_caps_wait_on_future_stamp(self):
        with tempfile.TemporaryDirectory() as d:
            stamp = os.path.join(d, "stamp")
            with open(stamp, "w") as fh:
                fh.write("9e9")
            t = ef.SharedThrottle(stamp, per_second=8)
            with mock.patch("time.sleep") as sl:
                t.wait()
            sl.assert_called_once_with(t.interval)

    def test_shared_throttle_falls_back_without_fcntl(self):
        with tempfile.TemporaryDirectory() as d:
            stamp = os.path.join(d, "stamp")
            t = ef.SharedThrottle(stamp, per_second=8)
            with mock.patch.dict(sys.modules, {"fcntl": None}), mock.patch.object(t._local, "wait", return_value=None) as lw:
                self.assertIsNone(t.wait())
            lw.assert_called_once()
            self.assertFalse(os.path.exists(stamp))

    def test_shared_throttle_falls_back_when_stamp_unopenable(self):
        with tempfile.TemporaryDirectory() as d:
            t = ef.SharedThrottle(os.path.join(d, "missing-dir", "stamp"), per_second=8)
            with mock.patch.object(t._local, "wait", return_value=None) as lw:
                self.assertIsNone(t.wait())
            lw.assert_called_once()

    def test_shared_throttle_falls_back_when_lock_fails(self):
        import errno
        import fcntl
        with tempfile.TemporaryDirectory() as d:
            t = ef.SharedThrottle(os.path.join(d, "stamp"), per_second=8)
            with mock.patch.object(fcntl, "flock", side_effect=OSError(errno.ENOLCK, "no locks")), \
                    mock.patch.object(t._local, "wait", return_value=None) as lw:
                self.assertIsNone(t.wait())
            lw.assert_called_once()

    def test_default_throttle_path_prefers_shared_storage(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.dict(os.environ, {"AGENT_SHARED_STORAGE_DIR": d}):
                self.assertEqual(ef.default_throttle_path(), Path(d) / "edgar-throttle")
        with mock.patch.dict(os.environ, {"AGENT_SHARED_STORAGE_DIR": ""}):
            self.assertIn("manigent-edgar-throttle-", ef.default_throttle_path().name)

    def test_frames_url_uses_per_unit(self):
        args = mock.Mock(tag="EarningsPerShareDiluted", taxonomy=None, unit="USD/shares", period="CY2025")
        self.assertTrue(ef.fetch_url("frames", args).endswith("/USD-per-shares/CY2025.json"))
        args.period = "2025"
        with self.assertRaises(SystemExit):
            ef.fetch_url("frames", args)

    def test_ticker_map_offline(self):
        doc = {"0": {"cik_str": 42, "ticker": "SYNW", "title": "Synthetic Widgets Inc."}}
        self.assertEqual(ef.ticker_to_cik("synw", doc)[0]["cik"], "0000000042")


if __name__ == "__main__":
    unittest.main()
