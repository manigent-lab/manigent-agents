# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Manigent Contributors
"""Unit tests for market_inputs.py on synthetic files (no network).

Run: python3 -m pytest test_market_inputs.py   (or python3 -m unittest test_market_inputs)
Every rate below is invented; only the file layouts follow the real sources.
"""
import io
import os
import sys
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import market_inputs as mi  # noqa: E402

TREASURY_CSV = (
    'Date,"1 Mo","2 Mo","3 Mo","1 Yr","2 Yr","5 Yr","10 Yr","20 Yr","30 Yr"\n'
    "10/02/2026,4.10,4.10,4.20,4.40,4.70,5.00,5.20,5.60,5.55\n"
    "10/01/2026,4.11,4.11,4.21,4.41,4.71,5.01,5.21,5.61,\n"
    "09/30/2026,4.12,4.12,4.22,4.42,4.72,5.02,5.22,5.62,5.57\n"
)


def _cell(ref, value):
    if isinstance(value, str):
        return f'<c r="{ref}" t="inlineStr"><is><t>{value}</t></is></c>'
    return f'<c r="{ref}"><v>{value}</v></c>'


def make_erp_xlsx(rows, date1904=True, sheet="Historical ERP"):
    """A minimal workbook laid out like ERPbymonth.xlsx: month serial, T.Bond Rate, variants."""
    header = ["Start of month", "S&amp;P 500", "T.Bond Rate", "ERP (T12 m with sustainable payout)",
              "ERP (T12m)", "ERP (T12m) with adj riskfree rate", "ERP (Smoothed)", "ERP (Normalized)",
              "ERP (Net Cash Yield)"]
    cols = "ABCDEFGHI"
    xml_rows = ['<row r="1">' + "".join(_cell(f"{c}1", h) for c, h in zip(cols, header)) + "</row>"]
    for i, r in enumerate(rows, start=2):
        xml_rows.append(f'<row r="{i}">' + "".join(_cell(f"{c}{i}", v) for c, v in zip(cols, r)
                                                   if v is not None) + "</row>")
    m = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/workbook.xml",
                   f'<workbook xmlns="{m}" xmlns:r="{r}"><workbookPr date1904="{int(date1904)}"/>'
                   f'<sheets><sheet name="Other" sheetId="2" r:id="rId2"/>'
                   f'<sheet name="{sheet}" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="worksheet" Target="worksheets/sheet1.xml"/>'
                   '<Relationship Id="rId2" Type="worksheet" Target="worksheets/sheet2.xml"/>'
                   '</Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="{m}"><sheetData>{"".join(xml_rows)}'
                                               "</sheetData></worksheet>")
        z.writestr("xl/worksheets/sheet2.xml", f'<worksheet xmlns="{m}"><sheetData/></worksheet>')
    return buf.getvalue()


def serial(d, date1904=True):
    base = date(1904, 1, 1) if date1904 else date(1899, 12, 30)
    return (d - base).days


# Aug, Sep, Oct 2026 months; headline / t12m variants differ so the column choice is visible.
ERP_ROWS = [
    [serial(date(2026, 8, 1)), 7500, 0.0450, 0.0430, 0.0420, 0.0440, 0.0600, 0.0360, 0.0390],
    [serial(date(2026, 9, 1)), 7600, 0.0475, 0.0414, 0.0409, 0.0431, 0.0605, 0.0356, 0.0380],
    [serial(date(2026, 10, 1)), 7650, 0.0529, 0.0420, 0.0370, 0.0392, 0.0567, 0.0330, 0.0361],
]


class Treasury(unittest.TestCase):
    rows = mi.parse_treasury_csv(TREASURY_CSV)

    def test_exact_day_and_decimal_value(self):
        obs = mi.treasury_obs(self.rows, date(2026, 10, 1), "10y")
        self.assertEqual((obs["value"], obs["as_of"]), (0.0521, "2026-10-01"))
        self.assertIn("10 Yr", obs["series"])

    def test_weekend_falls_back_to_prior_observation(self):
        obs = mi.treasury_obs(self.rows, date(2026, 10, 4), "2y")
        self.assertEqual((obs["as_of"], obs["requested_as_of"]), ("2026-10-02", "2026-10-04"))

    def test_blank_cell_skips_to_last_day_with_a_value(self):
        obs = mi.treasury_obs(self.rows, date(2026, 10, 1), "30y")
        self.assertEqual(obs["as_of"], "2026-09-30")

    def test_before_data_and_unknown_tenor_raise(self):
        with self.assertRaises(mi.InputError):
            mi.treasury_obs(self.rows, date(2026, 9, 1), "10y")
        with self.assertRaises(mi.InputError):
            mi.treasury_obs(self.rows, date(2026, 10, 1), "15y")

    def test_saved_csv_path_needs_no_network(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(mi, "http_get") as get:
            p = Path(d, "t.csv")
            p.write_text(TREASURY_CSV)
            obs = mi.treasury(date(2026, 10, 2), "5y", str(p))
            get.assert_not_called()
        self.assertEqual(obs["value"], 0.05)

    def test_early_january_reaches_into_prior_year_file(self):
        prior = 'Date,"10 Yr"\n12/31/2025,4.18\n'
        calls = []

        def fake_get(url):
            calls.append(url)
            return (b'Date,"10 Yr"\n' if "/2026/" in url else prior.encode()), "2026-01-02"

        with mock.patch.object(mi, "http_get", fake_get):
            obs = mi.treasury(date(2026, 1, 1), "10y")
        self.assertEqual((obs["as_of"], obs["value"]), ("2025-12-31", 0.0418))
        self.assertEqual(len(calls), 2)


class Erp(unittest.TestCase):
    xlsx = make_erp_xlsx(ERP_ROWS)

    def test_point_in_time_picks_month_on_or_before(self):
        obs = mi.erp_obs(self.xlsx, date(2026, 9, 30))
        self.assertEqual((obs["value"], obs["as_of"]), (0.0414, "2026-09-01"))
        self.assertEqual(obs["riskfree_used"], 0.0475)

    def test_named_variant_reads_its_own_column(self):
        obs = mi.erp_obs(self.xlsx, date(2026, 10, 11), "t12m")
        self.assertEqual((obs["value"], obs["variant"]), (0.037, "t12m"))
        self.assertIn("ERP (T12m)", obs["series"])

    def test_1904_and_1900_date_systems(self):
        rows1900 = [[serial(date(2026, 9, 1), False)] + ERP_ROWS[1][1:]]
        obs = mi.erp_obs(make_erp_xlsx(rows1900, date1904=False), date(2026, 9, 15))
        self.assertEqual(obs["as_of"], "2026-09-01")
        # The same serial read under the wrong system would land four years off.
        self.assertEqual(mi.excel_date(ERP_ROWS[1][0], True), date(2026, 9, 1))

    def test_missing_sheet_or_variant_raises(self):
        with self.assertRaises(mi.InputError):
            mi.erp_obs(make_erp_xlsx(ERP_ROWS, sheet="Renamed"), date(2026, 10, 1))
        with self.assertRaises(mi.InputError):
            mi.erp_obs(self.xlsx, date(2026, 10, 1), "five-to-six-percent")
        with self.assertRaises(mi.InputError):
            mi.erp_obs(self.xlsx, date(2026, 7, 31))


class WaccInputs(unittest.TestCase):
    def _run(self, as_of):
        with tempfile.TemporaryDirectory() as d:
            c, x = Path(d, "t.csv"), Path(d, "e.xlsx")
            c.write_text(TREASURY_CSV)
            x.write_bytes(make_erp_xlsx(ERP_ROWS))
            return mi.wacc_inputs(as_of, csv_path=str(c), xlsx_path=str(x))

    def test_same_series_warning_when_riskfree_diverges(self):
        out = self._run(date(2026, 9, 30))  # Sep ERP used 4.75%; Treasury on 9/30 is 5.22%
        self.assertEqual(len(out["warnings"]), 1)
        self.assertIn("4.75%", out["warnings"][0])

    def test_no_warning_when_series_agree(self):
        out = self._run(date(2026, 10, 2))  # Oct ERP used 5.29%; Treasury 5.20%
        self.assertEqual(out["warnings"], [])

    def test_same_series_check_skipped_off_10y(self):
        with tempfile.TemporaryDirectory() as d:
            c, x = Path(d, "t.csv"), Path(d, "e.xlsx")
            c.write_text(TREASURY_CSV)
            x.write_bytes(make_erp_xlsx(ERP_ROWS))
            out = mi.wacc_inputs(date(2026, 9, 30), tenor="30y", csv_path=str(c), xlsx_path=str(x))
        self.assertEqual(out["warnings"], [])


class Robustness(unittest.TestCase):
    def test_csv_with_bom(self):
        with tempfile.TemporaryDirectory() as d:
            c = Path(d, "t.csv")
            c.write_bytes(b"\xef\xbb\xbf" + TREASURY_CSV.encode())
            self.assertEqual(mi.treasury(date(2026, 9, 30), csv_path=str(c))["value"], 0.0522)

    def test_missing_sheet_rel_is_input_error(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(make_erp_xlsx(ERP_ROWS))) as src, zipfile.ZipFile(buf, "w") as z:
            for n in src.namelist():
                body = src.read(n)
                if n == "xl/_rels/workbook.xml.rels":
                    body = body.replace(b'Id="rId1"', b'Id="rId9"')
                z.writestr(n, body)
        with self.assertRaises(mi.InputError):
            mi.erp_obs(buf.getvalue(), date(2026, 9, 30))

    def test_shared_strings_skip_phonetic_runs_and_cells_without_ref(self):
        m = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        buf = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(make_erp_xlsx(ERP_ROWS))) as src, zipfile.ZipFile(buf, "w") as z:
            for n in src.namelist():
                if n != "xl/worksheets/sheet2.xml":
                    z.writestr(n, src.read(n))
            z.writestr("xl/sharedStrings.xml",
                       f'<sst xmlns="{m}"><si><r><t>Ka</t></r><r><t>na</t></r><rPh><t>PHON</t></rPh></si></sst>')
            z.writestr("xl/worksheets/sheet2.xml",
                       f'<worksheet xmlns="{m}"><sheetData><row r="1"><c t="s"><v>0</v></c>'
                       f'<c t="d"><v>2026-09-01</v></c></row></sheetData></worksheet>')
        rows, _ = mi._sheet_rows(buf.getvalue(), "Other")
        self.assertEqual(rows, [["Kana", "2026-09-01"]])


class Web(unittest.TestCase):
    def test_web_disabled_refuses_fetch(self):
        with mock.patch.dict(os.environ, {mi.WEB_DISABLED_ENV: "1"}), \
                mock.patch("urllib.request.urlopen") as op:
            with self.assertRaises(SystemExit):
                mi.http_get(mi.ERP_URL)
            op.assert_not_called()

    def test_last_modified_parsed_to_date(self):
        self.assertEqual(mi._http_date("Tue, 06 Oct 2026 20:24:02 GMT"), "2026-10-06")
        self.assertEqual(mi._http_date("garbage"), "")


if __name__ == "__main__":
    unittest.main()
