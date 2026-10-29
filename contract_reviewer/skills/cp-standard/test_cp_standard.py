# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Manigent Contributors
"""Unit tests for cp_standard.py on synthetic CSA files (no network).

Run: python3 -m pytest test_cp_standard.py   (or python3 -m unittest test_cp_standard)
The clause text below is invented; only the markup follows Common Paper's CSA.md.
"""
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cp_standard as cp  # noqa: E402


def h2(id_, title):
    return f'{id_}. <span class="header_2" id="{id_}">{title}</span>'


def h3(id_, title, body):
    n = id_.split(".")[-1]
    return f'    {n}. <span class="header_3" id="{id_}">{title}</span>  {body}'


OLD = "\n".join([
    "# Cloud Service Agreement", "",
    h2("4", "Payment"),
    h3("4.1", "Fees.", "Customer pays the Fees."),
    h3("4.2", "Invoicing.", "Provider sends invoices."),
    h3("4.3", "Taxes.", "Customer pays taxes."),
    h2("8", "Limitation of Liability"),
    h3("8.1", "Liability Caps.", ""),
    "        a. **Each party's liability is capped at the <span class=\"coverpage_link\">General Cap Amount</span>.**",
    "        b. **Increased Claims are capped at the Increased Cap Amount.**",
    h3("8.4", "Exceptions.", "Unlimited Claims are uncapped."),
    h2("13", "Definitions"),
    h3("13.1", "Defining Variables.", 'An undefined Variable means "none" and the clause does not apply.'),
    h3("13.2", '<strong>"Standard Terms"</strong>',
       "means these Common Paper Cloud Service Agreement Standard Terms Version 2.1, which are posted at ."),
    "",
])

NEW = "\n".join([
    "# Cloud Service Agreement", "",
    h2("4", "Payment"),
    h3("4.1", "Fees.", "Customer pays the Fees."),
    h3("4.2", "Taxes.", "Customer pays taxes."),
    h2("8", "Limitation of Liability"),
    h3("8.1", "Liability Cap.", "**Except as provided in the Cover Page, liability is capped at the General Cap Amount.**"),
    h3("8.4", "Exceptions.", "Nothing limits liability for fraud."),
    h2("13", "Definitions"),
    h3("13.1", '<strong>"Standard Terms"</strong>',
       "means these Common Paper Cloud Service Agreement Standard Terms Version 3.0, which are posted at ."),
    "",
])


def fake_get(url):
    if url == cp.TAGS_URL:
        return ("001e# service=git-upload-pack\n0000" + "".join(
            f"003f{'0' * 40} refs/tags/{t}\n" for t in ("2.1", "1.0", "2.0", "1.1")) + "0000")
    if "/2.1/" in url:
        return OLD
    if f"/{cp.PINNED['3.0']}/" in url or "/main/" in url:
        return NEW
    raise cp.NotFound(f"HTTP 404 for {url}")


class ParseTests(unittest.TestCase):
    def test_version_and_sections(self):
        t = cp.parse_terms(OLD)
        self.assertEqual(t["version"], "2.1")
        self.assertEqual(t["sections"]["13.1"]["heading"], "Defining Variables")
        self.assertEqual(t["sections"]["13.2"]["heading"], "Standard Terms")

    def test_sub_items_stay_with_parent_and_markup_is_stripped(self):
        text = cp.parse_terms(OLD)["sections"]["8.1"]["text"]
        self.assertIn("a. Each party's liability is capped at the General Cap Amount.", text)
        self.assertIn("b. Increased Claims", text)
        self.assertNotIn("<span", text)
        self.assertNotIn("**", text)

    def test_not_a_csa_fails_loudly(self):
        with self.assertRaisesRegex(cp.InputError, "no section anchors"):
            cp.parse_terms("# Some other document\n\n1. Plain numbered text\n")


class LoadTests(unittest.TestCase):
    def test_tagged_version_uses_its_tag(self):
        with mock.patch.object(cp, "http_get", side_effect=fake_get) as get:
            t = cp.load("2.1")
        self.assertEqual(t["ref"], "2.1")
        self.assertIn("/CSA/2.1/CSA.md", get.call_args[0][0])
        self.assertTrue(t["page_url"].endswith("/cloud-service-agreement/2.1"))

    def test_untagged_version_uses_its_pinned_commit(self):
        with mock.patch.object(cp, "http_get", side_effect=fake_get) as get:
            t = cp.load("3.0")
        self.assertEqual(t["ref"], cp.PINNED["3.0"])
        self.assertNotIn("/main/", get.call_args[0][0])

    def test_unknown_version_is_taken_from_main_only_if_main_says_so(self):
        main_31 = NEW.replace("Version 3.0", "Version 3.1")
        get = lambda url: main_31 if "/main/" in url else fake_get(url)
        with mock.patch.object(cp, "http_get", side_effect=get):
            self.assertEqual(cp.load("3.1")["ref"], "main")
            with self.assertRaisesRegex(cp.InputError, "main is version 3.1"):
                cp.load("3.2")

    def test_tag_wins_once_a_pinned_version_is_tagged(self):
        # Common Paper tags 3.0 and main moves on to 3.1: 3.0 must still resolve, at its tag.
        main_31 = NEW.replace("Version 3.0", "Version 3.1")
        get = lambda url: NEW if "/3.0/" in url else main_31 if "/main/" in url else fake_get(url)
        with mock.patch.object(cp, "http_get", side_effect=get):
            self.assertEqual(cp.load("3.0")["ref"], "3.0")

    def test_saved_file_and_version_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "CSA.md"
            f.write_bytes(b"\xef\xbb\xbf" + NEW.encode())  # a BOM must not matter
            self.assertEqual(cp.load(None, str(f))["version"], "3.0")
            with self.assertRaisesRegex(cp.InputError, "is version 3.0, not 2.1"):
                cp.load("2.1", str(f))

    def test_web_disabled_refuses_fetch(self):
        with mock.patch.dict(os.environ, {cp.WEB_DISABLED_ENV: "1"}):
            with self.assertRaisesRegex(cp.InputError, "--file"):
                cp.load("2.1")


class SectionTests(unittest.TestCase):
    def test_top_level_id_returns_every_subsection(self):
        out = cp.section(cp.parse_terms(OLD), ["8"])["sections"][0]
        self.assertEqual(out["heading"], "Limitation of Liability")
        self.assertIn("8.1 Liability Caps.", out["text"])
        self.assertIn("8.4 Exceptions.", out["text"])

    def test_prefix_does_not_overmatch(self):
        t = cp.parse_terms(OLD)
        t["sections"]["13.10"] = {"heading": "Ten", "text": "x"}
        self.assertNotIn("Ten", cp.section(t, ["13.1"])["sections"][0]["text"])

    def test_unknown_section(self):
        with self.assertRaisesRegex(cp.InputError, "no section 9.9 in version 2.1"):
            cp.section(cp.parse_terms(OLD), ["9.9"])


class DiffTests(unittest.TestCase):
    def setUp(self):
        self.changes = {c.get("from_id") or c.get("to_id"): c
                        for c in cp.diff(cp.parse_terms(OLD), cp.parse_terms(NEW))["changes"]}

    def test_removed_retitled_renumbered(self):
        self.assertEqual(self.changes["4.2"]["status"], "removed")            # Invoicing
        self.assertEqual(self.changes["4.3"], {"status": "renumbered", "from_id": "4.3", "to_id": "4.2",
                                               "heading": "Taxes"})
        self.assertEqual(self.changes["8.1"]["status"], "retitled+changed")
        self.assertEqual(self.changes["8.1"]["to_heading"], "Liability Cap")
        self.assertEqual(self.changes["8.4"]["status"], "changed")

    def test_number_reused_by_another_clause_is_a_removal(self):
        # 13.1 "Defining Variables" is gone; "Standard Terms" moved up into 13.1.
        self.assertEqual(self.changes["13.1"]["status"], "removed")
        self.assertEqual(self.changes["13.2"]["status"], "renumbered+changed")
        self.assertEqual(self.changes["13.2"]["to_id"], "13.1")

    def test_unchanged_section_is_not_listed_and_text_is_opt_in(self):
        self.assertNotIn("4.1", self.changes)
        self.assertNotIn("from_text", self.changes["8.4"])
        full = cp.diff(cp.parse_terms(OLD), cp.parse_terms(NEW), with_text=True)["changes"]
        exc = next(c for c in full if c.get("from_id") == "8.4")
        self.assertIn("Unlimited Claims", exc["from_text"])
        self.assertIn("fraud", exc["to_text"])
        retitled_same = cp.diff(cp.parse_terms(OLD.replace("Liability Caps.", "Caps.")),
                                cp.parse_terms(OLD.replace("Liability Caps.", "Cap.")))["changes"]
        self.assertEqual([c["status"] for c in retitled_same], ["retitled"])

    def test_repeated_heading_pairs_within_its_article(self):
        # "Fees" is both section 4.1 and definition 13.3. If 4.1 is deleted, the old 4.1 must
        # be reported as removed, not as moved into the definitions.
        old = OLD.replace(h2("13", "Definitions"), h2("13", "Definitions") + "\n" + h3("13.9", "Fees", "means fees."))
        new = NEW.replace(h3("4.1", "Fees.", "Customer pays the Fees.") + "\n", "").replace(
            h2("13", "Definitions"), h2("13", "Definitions") + "\n" + h3("13.9", "Fees", "means fees."))
        changes = {c.get("from_id"): c for c in cp.diff(cp.parse_terms(old), cp.parse_terms(new))["changes"]}
        self.assertEqual(changes["4.1"]["status"], "removed")
        self.assertNotIn("13.9", changes)

    def test_added_section(self):
        new = NEW.replace(h2("13", "Definitions"),
                          h3("8.5", "Insurance.", "Provider keeps insurance.") + "\n" + h2("13", "Definitions"))
        added = [c for c in cp.diff(cp.parse_terms(OLD), cp.parse_terms(new))["changes"] if c["status"] == "added"]
        self.assertEqual(added, [{"status": "added", "to_id": "8.5", "heading": "Insurance"}])


class DetectTests(unittest.TestCase):
    def _write(self, d, name, text):
        p = Path(d) / name
        p.write_text(text)
        return str(p)

    def test_cover_page_version(self):
        with tempfile.TemporaryDirectory() as d:
            f = self._write(d, "cover.txt", "COMMON PAPER CLOUD SERVICE AGREEMENT - COVER PAGE "
                                            "(STANDARD TERMS VERSION 2.1)\nGeneral Cap Amount: ~~1x~~\n")
            out = cp.detect(f)
        self.assertEqual(out["versions"], ["2.1"])
        self.assertIsNone(out["note"])
        self.assertEqual(out["mentions"][0]["line"], 1)

    def test_none_and_conflicting(self):
        with tempfile.TemporaryDirectory() as d:
            none = cp.detect(self._write(d, "a.txt", "Master Subscription Agreement\n"))
            both = cp.detect(self._write(d, "b.md", "Cloud Service Agreement Version 2.1\n\n"
                                                    "means these Standard Terms Version 3.0\n"))
        self.assertEqual(none["versions"], [])
        self.assertIn("ask which one", none["note"])
        self.assertEqual(both["versions"], ["2.1", "3.0"])
        self.assertIn("more than one", both["note"])

    def test_docx(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.docx"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("word/document.xml",
                           '<w:document><w:body><w:p><w:r><w:t>Common Paper Cloud Service Agreement '
                           '</w:t></w:r><w:r><w:t>Version 3.0</w:t></w:r></w:p></w:body></w:document>')
            self.assertEqual(cp.detect(str(p))["versions"], ["3.0"])

    def test_csa_abbreviation_and_v_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            out = cp.detect(self._write(d, "a.txt", "This Order Form is under the Common Paper CSA v3.0.\n"))
        self.assertEqual(out["versions"], ["3.0"])

    def test_docx_tab_or_break_between_word_and_number(self):
        with tempfile.TemporaryDirectory() as d:
            for sep in ("<w:tab/>", "<w:br/>"):
                p = Path(d) / "c.docx"
                with zipfile.ZipFile(p, "w") as z:
                    z.writestr("word/document.xml",
                               '<w:document><w:body><w:p><w:r><w:t>Standard Terms Version</w:t></w:r>'
                               f'<w:r>{sep}<w:t>3.0</w:t></w:r></w:p></w:body></w:document>')
                self.assertEqual(cp.detect(str(p))["versions"], ["3.0"], sep)

    def test_another_documents_version_is_not_the_csa_version(self):
        with tempfile.TemporaryDirectory() as d:
            out = cp.detect(self._write(d, "a.txt", "Order Form under the Cloud Service Agreement and the "
                                                    "DPA Version 1.1\nStandard Terms Version 2.1\n"))
        self.assertEqual(out["versions"], ["2.1"])
        self.assertIsNone(out["note"])

    def test_cloud_security_alliance_reference_is_not_a_csa_version(self):
        with tempfile.TemporaryDirectory() as d:
            out = cp.detect(self._write(d, "a.txt", "Standard Terms Version 3.0\n"
                                                    "Provider's controls align to the CSA CCM v4.0.\n"))
        self.assertEqual(out["versions"], ["3.0"])
        self.assertIsNone(out["note"])

    def test_defined_term_aside_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            out = cp.detect(self._write(d, "a.txt", 'Common Paper Cloud Service Agreement '
                                                    '(the "Agreement") Version 3.0\n'))
        self.assertEqual(out["versions"], ["3.0"])


class CliTests(unittest.TestCase):
    def test_error_exit_status(self):
        err = io.StringIO()
        with mock.patch.object(cp, "http_get", side_effect=fake_get), redirect_stderr(err):
            self.assertEqual(cp.main(["section", "--version", "2.5", "--id", "1"]), 2)
        self.assertIn("error: version 2.5", err.getvalue())

    def test_versions(self):
        out = io.StringIO()
        with mock.patch.object(cp, "http_get", side_effect=fake_get), redirect_stdout(out):
            self.assertEqual(cp.main(["versions"]), 0)
        got = json.loads(out.getvalue())
        self.assertEqual(got["tagged"], ["1.0", "1.1", "2.0", "2.1"])
        self.assertEqual(got["untagged_current"], "3.0")


if __name__ == "__main__":
    unittest.main()
