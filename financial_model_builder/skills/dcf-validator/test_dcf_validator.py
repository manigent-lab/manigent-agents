# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Manigent Contributors
"""Unit tests for dcf_validator.py on synthetic inputs. Run: python3 -m pytest test_dcf_validator.py"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dcf_validator as dv  # noqa: E402

try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None


def found(**kw):
    return {k: (v, "test") for k, v in kw.items()}


def checks(findings, sev):
    return {f["check"] for f in findings if f["severity"] == sev}


class Validate(unittest.TestCase):
    def test_growth_at_or_above_wacc_is_critical(self):
        self.assertIn("growth_vs_wacc", checks(dv.validate(found(wacc=0.06, terminal_growth=0.06)), "critical"))
        self.assertNotIn("growth_vs_wacc", checks(dv.validate(found(wacc=0.06, terminal_growth=0.02)), "critical"))

    def test_growth_above_riskfree_warns(self):
        f = dv.validate(found(wacc=0.09, terminal_growth=0.05), riskfree=0.04)
        self.assertIn("growth_vs_riskfree", checks(f, "warning"))

    def test_percent_stored_as_whole_number(self):
        f = dv.validate(found(wacc=9.0, terminal_growth=2.0))
        self.assertIn("percent_as_whole_number", checks(f, "warning"))
        self.assertNotIn("growth_vs_wacc", checks(f, "critical"))

    def test_wacc_band_and_tv_share(self):
        f = dv.validate(found(wacc=0.30, pv_terminal_value=80, enterprise_value=100))
        self.assertEqual(checks(f, "warning"), {"wacc_band", "tv_share_of_ev"})

    def test_mid_year_switch_vs_periods(self):
        f = dv.validate(found(mid_year=True, discount_periods=[1, 2, 3]))
        self.assertIn("mid_year_mismatch", checks(f, "critical"))
        f = dv.validate(found(mid_year=True, discount_periods=[0.5, 1.5, 2.5]))
        self.assertNotIn("mid_year_mismatch", checks(f, "critical"))

    def test_stub_schedules_are_recognised(self):
        s = 0.25
        mid = dv.validate(found(discount_periods=[s / 2, s + 0.5, s + 1.5]))
        end = dv.validate(found(discount_periods=[s, s + 1, s + 2]))
        self.assertIn("mid-year", next(x["detail"] for x in mid if x["check"] == "discount_convention"))
        self.assertIn("end-year", next(x["detail"] for x in end if x["check"] == "discount_convention"))

    def test_tv_exponent_detection(self):
        w, tv, n = 0.1, 1000.0, 5
        periods = [0.5, 1.5, 2.5, 3.5, 4.5]
        at_end = dv.validate(found(wacc=w, terminal_value=tv, pv_terminal_value=tv / (1 + w) ** n,
                                   discount_periods=periods, mid_year=True, terminal_growth=0.02))
        self.assertIn("tv_timing", checks(at_end, "info"))
        exit_mid = dv.validate(found(wacc=w, terminal_value=tv, pv_terminal_value=tv / (1 + w) ** (n - 0.5),
                                     discount_periods=periods, mid_year=True, exit_multiple=8.0))
        self.assertIn("tv_timing", checks(exit_mid, "warning"))
        wrong = dv.validate(found(wacc=w, terminal_value=tv, pv_terminal_value=tv / (1 + w) ** (n - 1),
                                  discount_periods=periods, mid_year=True, terminal_growth=0.02))
        self.assertIn("tv_timing", checks(wrong, "critical"))

    def test_missing_inputs_reported(self):
        f = dv.validate({})
        self.assertIn("inputs_not_found", checks(f, "info"))

    def test_json_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "in.json"
            p.write_text(json.dumps({"wacc": 0.05, "terminal_growth": 0.05}))
            self.assertEqual(dv.main(["--json", str(p)]), 1)
            p.write_text(json.dumps({"wacc": 0.08, "terminal_growth": 0.02, "mid_year": "yes",
                                     "discount_periods": [0.5, 1.5]}))
            self.assertEqual(dv.main(["--json", str(p), "--format", "table"]), 0)


@unittest.skipIf(openpyxl is None, "openpyxl not installed")
class Xlsx(unittest.TestCase):
    def test_labels_located_and_errors_flagged(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "DCF"
        ws.append(["Discount rate (WACC)", None, 0.09])
        ws.append(["Terminal growth rate", None, "2.0%"])
        ws.append(["Risk-free rate", None, 0.04])
        ws.append(["Mid-year convention", "Yes"])
        ws.append(["Discount period", 0.5, 1.5, 2.5])
        ws.append(["Terminal value", None, 1000])
        ws.append(["PV of terminal value", None, 1000 / 1.09 ** 3])
        ws.append(["Enterprise value", None, 1000])
        ws["E1"] = "#DIV/0!"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "dcf.xlsx"
            wb.save(p)
            got, pre = dv.read_xlsx(str(p), None)
        self.assertAlmostEqual(got["terminal_growth"][0], 0.02)
        self.assertEqual(got["mid_year"][0], True)
        self.assertEqual(got["discount_periods"][0], [0.5, 1.5, 2.5])
        self.assertEqual(pre[0]["check"], "error_value")
        f = dv.validate(got)
        self.assertIn("tv_share_of_ev", checks(f, "warning"))
        self.assertIn("tv_timing", checks(f, "info"))


if __name__ == "__main__":
    unittest.main()
