# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Manigent Contributors
"""Unit tests for valuation_calc.py. Run: python3 -m pytest test_valuation_calc.py

Inputs are arbitrary synthetic numbers; each test checks an identity or a convention
(closed form, round trip, invariance) rather than a worked valuation.
"""
import contextlib
import io
import json
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import valuation_calc as vc  # noqa: E402


class CostOfCapital(unittest.TestCase):
    def test_unlever_relever_round_trip(self):
        bu = vc.unlever_beta(1.3, 0.4, 0.25)
        self.assertAlmostEqual(vc.relever_beta(bu, 0.4, 0.25), 1.3)
        self.assertLess(bu, 1.3)

    def test_cash_corrected_beta_rises_with_cash(self):
        self.assertGreater(vc.cash_corrected_beta(0.9, 10, 100), 0.9)
        with self.assertRaises(ValueError):
            vc.cash_corrected_beta(0.9, 100, 100)

    def test_capm_components(self):
        self.assertAlmostEqual(vc.capm(0.03, 1.0, 0.05), 0.08)
        self.assertAlmostEqual(vc.capm(0.03, 1.0, 0.05, crp=0.02, crp_exposure=0.5), 0.09)

    def test_disallowed_interest_gets_no_shield(self):
        self.assertAlmostEqual(vc.after_tax_cost_of_debt(0.08, 0.25, deductible_share=0.0), 0.08)
        self.assertAlmostEqual(vc.after_tax_cost_of_debt(0.08, 0.25), 0.06)

    def test_wacc_weights_sum_to_one(self):
        r = vc.wacc(300, 100, 0.10, 0.04, preferred_value=50, cost_of_preferred=0.07)
        self.assertAlmostEqual(r["weight_equity"] + r["weight_debt"] + r["weight_preferred"], 1.0)
        lo, hi = min(0.10, 0.04, 0.07), max(0.10, 0.04, 0.07)
        self.assertTrue(lo < r["wacc"] < hi)


class Discounting(unittest.TestCase):
    def test_mid_year_exponents(self):
        self.assertEqual(vc.discount_exponents(3, "mid"), [0.5, 1.5, 2.5])
        self.assertEqual(vc.discount_exponents(3, "end"), [1, 2, 3])

    def test_stub_exponents(self):
        s = 0.25
        self.assertEqual(vc.discount_exponents(3, "mid", s), [s / 2, s + 0.5, s + 1.5])
        self.assertEqual(vc.discount_exponents(3, "end", s), [s, s + 1, s + 2])

    def test_factors_match_closed_form(self):
        r = 0.093
        f = vc.discount_factors(r, 4, "mid")
        for t, x in enumerate(f, 1):
            self.assertAlmostEqual(x, 1 / (1 + r) ** (t - 0.5))

    def test_mid_year_pv_is_end_year_pv_times_half_year(self):
        flows, r = [7, 8, 9], 0.11
        mid = vc.present_value(flows, r, "mid")["pv"]
        end = vc.present_value(flows, r, "end")["pv"]
        self.assertAlmostEqual(mid, end * (1 + r) ** 0.5)

    def test_prorate_first(self):
        out = vc.present_value([40, 50], 0.1, "end", stub=0.5, prorate_first=True)
        self.assertEqual(out["flows_used"], [20, 50])

    def test_bad_conventions_rejected(self):
        with self.assertRaises(ValueError):
            vc.discount_exponents(3, "middle")
        with self.assertRaises(ValueError):
            vc.discount_exponents(3, "mid", stub=0)

    def test_unlevered_fcf_identity(self):
        self.assertAlmostEqual(vc.unlevered_fcf(50, 0.2, 5, 8, 2), 50 * 0.8 + 5 - 8 - 2)
        self.assertAlmostEqual(vc.unlevered_fcf(50, 0.2, 5, 8, 2, cash_taxes=4), 50 - 4 + 5 - 8 - 2)


class Terminal(unittest.TestCase):
    def test_gordon_requires_g_below_r(self):
        with self.assertRaises(ValueError):
            vc.gordon_terminal_value(10, 0.05, 0.05)
        self.assertAlmostEqual(vc.gordon_terminal_value(10, 0.09, 0.02), 10 / 0.07)

    def test_exit_tv_is_discounted_at_end_even_with_mid_year_flows(self):
        self.assertEqual(vc.terminal_exponent(5, "exit", "mid"), 5)
        self.assertEqual(vc.terminal_exponent(5, "exit", "mid", stub=0.5), 4.5)

    def test_gordon_timing_must_be_stated(self):
        with self.assertRaises(ValueError):
            vc.terminal_exponent(5, "gordon", "mid")
        self.assertEqual(vc.terminal_exponent(5, "gordon", "mid", gordon_discounting="mid"), 4.5)
        self.assertEqual(vc.terminal_exponent(5, "gordon", "mid", gordon_discounting="end"), 5)
        with self.assertRaises(ValueError):
            vc.terminal_exponent(5, "gordon", "end", gordon_discounting="mid")

    def test_terminal_flags(self):
        self.assertEqual(vc.terminal_checks(0.02, riskfree=0.04), [])
        flags = vc.terminal_checks(0.05, riskfree=0.04, roic=0.10, nopat_next=100, reinvestment_next=10,
                                   capex_terminal=5, d_and_a_terminal=6)
        self.assertEqual(len(flags), 3)


class Bridge(unittest.TestCase):
    def test_signs(self):
        r = vc.equity_bridge(1000, {"debt": 200, "nci": 30, "cash": 50, "equity_method_investments": 20})
        self.assertAlmostEqual(r["equity_value"], 1000 - 200 - 30 + 50 + 20)
        with self.assertRaises(ValueError):
            vc.equity_bridge(1000, {"goodwill": 1})
        with self.assertRaises(ValueError):
            vc.equity_bridge(1000, {"debt": -5})

    def test_tsm_closed_form_and_out_of_money(self):
        self.assertAlmostEqual(vc.treasury_stock_shares([(10, 20), (5, 60)], 40), 10 - 10 * 20 / 40)

    def test_dilution_fixed_point(self):
        eq, basic, opts, rsus = 1000.0, 50.0, [(6, 10.0)], 2.0
        r = vc.diluted_value_per_share(eq, basic, opts, rsus)
        p = r["value_per_share"]
        self.assertAlmostEqual(p * (basic + rsus + vc.treasury_stock_shares(opts, p)), eq, places=6)

    def test_convert_in_the_money_swaps_debt_for_shares(self):
        r = vc.diluted_value_per_share(800.0, 40.0, convertibles=[(100.0, 10.0)])  # conversion price 10
        self.assertEqual(r["converted"], [True])
        self.assertAlmostEqual(r["equity_value_used"], 900.0)
        self.assertAlmostEqual(r["diluted_shares"], 50.0)
        r2 = vc.diluted_value_per_share(800.0, 40.0, convertibles=[(1000.0, 10.0)])  # conversion price 100
        self.assertEqual(r2["converted"], [False])
        self.assertAlmostEqual(r2["equity_value_used"], 800.0)


class Returns(unittest.TestCase):
    def test_irr_round_trip(self):
        flows = [-100, 5, 5, 140]
        r = vc.irr(flows)
        self.assertAlmostEqual(vc.npv(r, flows), 0, places=8)

    def test_xirr_matches_irr_on_365_day_spacing(self):
        flows = [-100, 0, 0, 0, 0, 180]
        d0 = date(2031, 1, 1)
        dated = [((d0 + timedelta(days=365 * i)).isoformat(), cf) for i, cf in enumerate(flows)]
        self.assertAlmostEqual(vc.xirr(dated), vc.irr(flows), places=9)

    def test_irr_needs_sign_change(self):
        with self.assertRaises(ValueError):
            vc.irr([100, 10])

    def test_moic_and_exit_equity(self):
        self.assertAlmostEqual(vc.moic(250, 100), 2.5)
        self.assertAlmostEqual(vc.exit_equity(30, 8, 90, 4), 30 * 8 - 90 - 4)

    def test_sources_and_uses_plug(self):
        r = vc.sources_and_uses({"purchase_equity": 600, "refinance": 200, "fees": 30, "min_cash": 10},
                                {"term_loan": 400, "notes": 150, "rollover": 20})
        self.assertAlmostEqual(r["sponsor_equity"], 840 - 570)
        self.assertAlmostEqual(sum(r["sources"].values()), r["total_uses"])
        with self.assertRaises(ValueError):
            vc.sources_and_uses({"x": 10}, {"debt": 20})


class Interest(unittest.TestCase):
    def test_163j_limit_and_carryforward(self):
        r = vc.interest_limit_163j(50, 100, business_interest_income=2, carryforward_in=5)
        self.assertAlmostEqual(r["limit"], 2 + 30)
        self.assertAlmostEqual(r["deductible"], 32)
        self.assertAlmostEqual(r["disallowed_carryforward"], 55 - 32)

    def test_debt_schedule_sweep_order_and_pik(self):
        tr = [{"name": "TLB", "balance": 100, "rate": 0.1, "amort": 0.01, "sweep": True},
              {"name": "Notes", "balance": 50, "rate": 0.08, "sweep": False},
              {"name": "HoldCo", "balance": 20, "rate": 0.12, "pik": True}]
        out = vc.debt_schedule(tr, [40, 40])
        p1 = out["periods"][0]
        self.assertAlmostEqual(p1["cash_interest"]["TLB"], 10)
        self.assertAlmostEqual(p1["cash_interest"]["HoldCo"], 0)
        self.assertAlmostEqual(p1["end"]["HoldCo"], 20 * 1.12)                  # PIK accretes
        self.assertAlmostEqual(p1["sweep"]["Notes"], 0)                        # not prepayable
        excess = 40 - 10 - 4 - 1
        self.assertAlmostEqual(p1["sweep"]["TLB"], excess)
        self.assertAlmostEqual(p1["end"]["TLB"], 100 - 1 - excess)

    def test_debt_schedule_average_converges_and_flags_shortfall(self):
        tr = [{"name": "TL", "balance": 100, "rate": 0.1, "amort": 0.05, "sweep": True}]
        avg = vc.debt_schedule(tr, [30], interest_basis="average")["periods"][0]
        end = avg["end"]["TL"]
        self.assertAlmostEqual(avg["cash_interest"]["TL"], (100 + end) / 2 * 0.1, places=6)
        short = vc.debt_schedule(tr, [5])["periods"][0]
        self.assertAlmostEqual(short["revolver_need"], 10 + 5 - 5)


class Cli(unittest.TestCase):
    def run_cli(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = vc.main(list(argv))
        return code, buf.getvalue()

    def test_list_and_call(self):
        code, out = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertIn("terminal_exponent", out)
        code, out = self.run_cli("discount_exponents", json.dumps({"n_periods": 2, "timing": "mid"}))
        self.assertEqual((code, json.loads(out)), (0, [0.5, 1.5]))

    def test_errors_return_nonzero(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code, _ = self.run_cli("gordon_terminal_value", json.dumps({"next_year_fcf": 1, "rate": 0.02, "growth": 0.03}))
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
