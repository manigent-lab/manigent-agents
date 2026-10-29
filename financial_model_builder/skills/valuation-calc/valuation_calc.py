#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Manigent Contributors
"""General DCF / WACC / EV-bridge / LBO functions with explicit conventions.

Import it, or run one function on a JSON object of keyword arguments:

    python valuation_calc.py list                       # functions and their signatures
    python valuation_calc.py <function> '<json kwargs>'  # e.g. capm '{"rf":..,"beta":..,"erp":..}'
    python valuation_calc.py <function> @inputs.json

Every function that depends on a convention takes it as a required argument
(discount timing, terminal-value timing, SBC treatment is the caller's), so the
choice is always written down next to the number. Rates are decimals (0.05, not 5).

Stdlib only.
"""
from __future__ import annotations

import inspect
import json
import math
import sys
from datetime import date
from typing import Iterable

# ---------------------------------------------------------------- cost of capital


def capm(rf: float, beta: float, erp: float, crp: float = 0.0, crp_exposure: float = 1.0) -> float:
    """Cost of equity = rf + beta * ERP + exposure * CRP.

    rf and erp must come from the same series (same tenor the ERP was implied against).
    crp_exposure scales the country risk premium by revenue exposure or lambda."""
    return rf + beta * erp + crp_exposure * crp


def unlever_beta(levered_beta: float, debt_to_equity: float, tax_rate: float) -> float:
    """Hamada: beta_U = beta_L / (1 + (1 - t) * D/E), with MARKET D/E."""
    return levered_beta / (1.0 + (1.0 - tax_rate) * debt_to_equity)


def relever_beta(unlevered_beta: float, debt_to_equity: float, tax_rate: float) -> float:
    """beta_L = beta_U * (1 + (1 - t) * D/E), with the target's market D/E and marginal rate."""
    return unlevered_beta * (1.0 + (1.0 - tax_rate) * debt_to_equity)


def cash_corrected_beta(unlevered_beta: float, cash: float, firm_value: float) -> float:
    """Unlevered beta of the operating business: beta_U / (1 - cash / firm value)."""
    if not 0 <= cash < firm_value:
        raise ValueError("cash must be >= 0 and below firm value")
    return unlevered_beta / (1.0 - cash / firm_value)


def after_tax_cost_of_debt(pre_tax: float, marginal_tax_rate: float, deductible_share: float = 1.0) -> float:
    """Kd * (1 - t * share of interest that is deductible). Use the MARGINAL rate; interest
    disallowed (e.g. under the interest limit) gets no shield (deductible_share < 1)."""
    if not 0 <= deductible_share <= 1:
        raise ValueError("deductible_share must be within [0, 1]")
    return pre_tax * (1.0 - marginal_tax_rate * deductible_share)


def wacc(equity_value: float, debt_value: float, cost_of_equity: float, after_tax_cost_of_debt: float,
         preferred_value: float = 0.0, cost_of_preferred: float = 0.0) -> dict:
    """Market-value weighted average cost of capital. Include lease liabilities in
    debt_value only if lease cost is removed from the cash flows being discounted."""
    total = equity_value + debt_value + preferred_value
    if total <= 0:
        raise ValueError("capital must be positive")
    we, wd, wp = equity_value / total, debt_value / total, preferred_value / total
    return {"wacc": we * cost_of_equity + wd * after_tax_cost_of_debt + wp * cost_of_preferred,
            "weight_equity": we, "weight_debt": wd, "weight_preferred": wp}


# ---------------------------------------------------------------- discounting


def discount_exponents(n_periods: int, timing: str, stub: float = 1.0) -> list[float]:
    """Exponent for each forecast period t = 1..n.

    timing='end': stub, stub + 1, stub + 2, ...
    timing='mid': stub / 2, then stub + (t - 1) - 0.5 for t >= 2.
    stub is the fraction of a year in the first period (1.0 = a full first year)."""
    if timing not in ("end", "mid"):
        raise ValueError("timing must be 'end' or 'mid'")
    if not 0 < stub <= 1:
        raise ValueError("stub must be in (0, 1]")
    out = []
    for t in range(1, n_periods + 1):
        if timing == "end":
            out.append(stub + (t - 1))
        else:
            out.append(stub / 2.0 if t == 1 else stub + (t - 1) - 0.5)
    return out


def discount_factors(rate: float, n_periods: int, timing: str, stub: float = 1.0) -> list[float]:
    return [1.0 / (1.0 + rate) ** e for e in discount_exponents(n_periods, timing, stub)]


def present_value(cash_flows: list[float], rate: float, timing: str, stub: float = 1.0,
                  prorate_first: bool = False) -> dict:
    """PV of forecast flows. prorate_first multiplies the first flow by stub (use it when
    the first flow is a full-year figure but only `stub` of the year remains)."""
    flows = list(cash_flows)
    if prorate_first and flows:
        flows[0] *= stub
    exps = discount_exponents(len(flows), timing, stub)
    pvs = [cf / (1.0 + rate) ** e for cf, e in zip(flows, exps)]
    return {"pv": sum(pvs), "exponents": exps, "pv_by_period": pvs, "flows_used": flows}


def unlevered_fcf(ebit: float, tax_rate: float, d_and_a: float, capex: float, delta_nwc: float,
                  cash_taxes: float | None = None) -> float:
    """EBIT(1 - t) + D&A - capex - increase in NWC. capex and delta_nwc are magnitudes
    (an NWC increase is positive). Pass cash_taxes to use cash taxes on EBIT instead of t."""
    taxes = cash_taxes if cash_taxes is not None else ebit * tax_rate
    return ebit - taxes + d_and_a - capex - delta_nwc


# ---------------------------------------------------------------- terminal value


def gordon_terminal_value(next_year_fcf: float, rate: float, growth: float) -> float:
    """TV at the end of the last forecast year = FCF_{N+1} / (r - g). Requires g < r."""
    if growth >= rate:
        raise ValueError("terminal growth must be below the discount rate")
    return next_year_fcf / (rate - growth)


def exit_multiple_terminal_value(metric: float, multiple: float) -> float:
    """TV = multiple x terminal-year metric (a point-in-time transaction value)."""
    return metric * multiple


def terminal_exponent(n_periods: int, method: str, timing: str, stub: float = 1.0,
                      gordon_discounting: str | None = None) -> float:
    """Exponent used to discount TV.

    method='exit'   : always the END of period N (a transaction value at that date).
    method='gordon' : gordon_discounting must be given -
                      'end' (at N; the conservative choice) or
                      'mid' (same exponent as year N's mid-year flow; only with timing='mid')."""
    end_n = stub + (n_periods - 1)
    if method == "exit":
        return end_n
    if method != "gordon":
        raise ValueError("method must be 'gordon' or 'exit'")
    if gordon_discounting not in ("end", "mid"):
        raise ValueError("state the Gordon TV discounting: gordon_discounting='end' or 'mid'")
    if gordon_discounting == "mid":
        if timing != "mid":
            raise ValueError("gordon_discounting='mid' only makes sense with mid-year flows")
        return discount_exponents(n_periods, "mid", stub)[-1]
    return end_n


def terminal_checks(growth: float, riskfree: float | None = None, roic: float | None = None,
                    nopat_next: float | None = None, reinvestment_next: float | None = None,
                    capex_terminal: float | None = None, d_and_a_terminal: float | None = None) -> list[str]:
    """Audit flags for terminal assumptions (empty list = nothing flagged)."""
    flags = []
    if riskfree is not None and growth > riskfree:
        flags.append("terminal growth exceeds the long-run nominal riskfree rate")
    if roic and nopat_next is not None and reinvestment_next is not None and nopat_next:
        implied = growth / roic
        actual = reinvestment_next / nopat_next
        if abs(implied - actual) > 0.05:
            flags.append(f"reinvestment rate {actual:.4f} is inconsistent with g / ROIC = {implied:.4f}")
    if growth > 0 and capex_terminal is not None and d_and_a_terminal is not None and capex_terminal <= d_and_a_terminal:
        flags.append("terminal capex does not exceed D&A while growth is positive")
    return flags


# ---------------------------------------------------------------- EV to equity


BRIDGE_SIGNS = {
    "debt": -1, "finance_leases": -1, "operating_leases": -1, "preferred": -1, "nci": -1,
    "pension_deficit_after_tax": -1, "other_debt_like": -1,
    "cash": +1, "investments": +1, "equity_method_investments": +1, "non_operating_assets": +1,
    "nol_value": +1,
}


def equity_bridge(enterprise_value: float, items: dict[str, float]) -> dict:
    """Equity value = EV - debt-like items + cash and non-operating assets.

    items keys must be in BRIDGE_SIGNS; amounts are positive magnitudes. Include
    operating_leases only if lease cost was excluded from the flows that produced EV,
    and nol_value only if NOLs were not already used in the forecast."""
    lines, eq = [], enterprise_value
    for k, amt in items.items():
        if k not in BRIDGE_SIGNS:
            raise ValueError(f"unknown bridge item {k!r}; one of {sorted(BRIDGE_SIGNS)}")
        if amt < 0:
            raise ValueError(f"{k}: pass a positive magnitude")
        eq += BRIDGE_SIGNS[k] * amt
        lines.append({"item": k, "amount": BRIDGE_SIGNS[k] * amt})
    return {"enterprise_value": enterprise_value, "lines": lines, "equity_value": eq}


def treasury_stock_shares(options: Iterable[tuple[float, float]], price: float) -> float:
    """Net new shares from in-the-money options/warrants: n - n * strike / price per tranche.
    options = [(count, strike), ...]."""
    if price <= 0:
        raise ValueError("price must be positive")
    return sum(n - n * k / price for n, k in options if k < price)


def diluted_value_per_share(equity_value: float, basic_shares: float,
                            options: Iterable[tuple[float, float]] = (), rsus: float = 0.0,
                            convertibles: Iterable[tuple[float, float]] = (),
                            tol: float = 1e-10, max_iter: int = 1000) -> dict:
    """Solve the share-count circularity: price = equity / diluted shares, where TSM
    shares depend on price. Seeded with the basic count.

    equity_value has every convertible already subtracted as debt. convertibles =
    [(face_amount, conversion_shares)]: an in-the-money convert (value per share above
    face / shares) is added back to equity and its shares added (if-converted), never both
    kept as debt and added as shares. rsus are added in full."""
    options, convertibles = list(options), list(convertibles)
    price = equity_value / basic_shares
    for it in range(1, max_iter + 1):
        eq, shares = equity_value, basic_shares + rsus
        converted = []
        for face, conv_shares in convertibles:
            if price > face / conv_shares:
                eq += face
                shares += conv_shares
                converted.append(True)
            else:
                converted.append(False)
        shares += treasury_stock_shares(options, price) if price > 0 else 0.0
        new_price = eq / shares
        if abs(new_price - price) <= tol * max(1.0, abs(price)):
            return {"value_per_share": new_price, "diluted_shares": shares, "equity_value_used": eq,
                    "converted": converted, "iterations": it}
        price = new_price
    raise RuntimeError("share-count iteration did not converge")


# ---------------------------------------------------------------- returns


def moic(equity_proceeds: float, equity_invested: float) -> float:
    return equity_proceeds / equity_invested


def npv(rate: float, flows: list[float]) -> float:
    """Flows at t = 0, 1, 2, ... (evenly spaced)."""
    return sum(cf / (1.0 + rate) ** t for t, cf in enumerate(flows))


def _solve(f, lo: float = -0.9999, hi: float = 10.0, tol: float = 1e-12) -> float:
    flo, fhi = f(lo), f(hi)
    while flo * fhi > 0 and hi < 1e6:
        hi *= 2
        fhi = f(hi)
    if flo * fhi > 0:
        raise ValueError("no sign change: flows need at least one outflow and one inflow")
    for _ in range(500):
        mid = (lo + hi) / 2.0
        fm = f(mid)
        if abs(fm) < tol or (hi - lo) < tol:
            return mid
        if flo * fm < 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2.0


def irr(flows: list[float]) -> float:
    """IRR for evenly spaced flows (period 0 first)."""
    return _solve(lambda r: npv(r, flows))


def xirr(dated_flows: list[tuple[str, float]]) -> float:
    """XIRR with actual/365 day count, like Excel. dated_flows = [("YYYY-MM-DD", amount), ...]."""
    pts = [(date.fromisoformat(d) if isinstance(d, str) else d, cf) for d, cf in dated_flows]
    d0 = min(d for d, _ in pts)
    return _solve(lambda r: sum(cf / (1.0 + r) ** ((d - d0).days / 365.0) for d, cf in pts))


def sources_and_uses(uses: dict[str, float], sources_excl_sponsor: dict[str, float]) -> dict:
    """Sponsor equity is the plug that makes sources = uses."""
    total_uses = sum(uses.values())
    other = sum(sources_excl_sponsor.values())
    sponsor = total_uses - other
    if sponsor < 0:
        raise ValueError("debt and other sources exceed uses")
    return {"total_uses": total_uses, "sponsor_equity": sponsor,
            "sources": {**sources_excl_sponsor, "sponsor_equity": sponsor}, "total_sources": total_uses}


def exit_equity(exit_ebitda: float, exit_multiple: float, net_debt_at_exit: float, exit_fees: float = 0.0) -> float:
    return exit_ebitda * exit_multiple - net_debt_at_exit - exit_fees


def interest_limit_163j(business_interest_expense: float, adjusted_taxable_income: float,
                        business_interest_income: float = 0.0, floor_plan_interest: float = 0.0,
                        carryforward_in: float = 0.0, ati_share: float = 0.30) -> dict:
    """Deductible business interest = BII + 30% x ATI + floor-plan interest; the excess
    carries forward. ATI is the caller's (post-2024 US: D&A added back, EBITDA-like)."""
    cap = business_interest_income + ati_share * max(adjusted_taxable_income, 0.0) + floor_plan_interest
    total = business_interest_expense + carryforward_in
    allowed = min(total, cap)
    return {"limit": cap, "deductible": allowed, "disallowed_carryforward": total - allowed}


def debt_schedule(tranches: list[dict], cash_available: list[float], interest_basis: str = "beginning",
                  min_cash: float = 0.0, opening_cash: float = 0.0, max_iter: int = 200) -> dict:
    """Multi-tranche debt roll with mandatory amortization, PIK and a cash sweep.

    tranches (senior first): {"name", "balance", "rate", "amort" (fraction of the ORIGINAL
    balance per period), "sweep" (True if prepayable), "pik" (True: interest accretes)}.
    cash_available[t] = cash flow before debt service in period t (after taxes).
    sweep: every unit of excess cash (after cash interest and mandatory amortization, above
    min_cash) prepays sweep-eligible tranches in order. interest_basis 'beginning' avoids
    the circularity; 'average' solves it by fixed-point iteration (the model then needs an
    iteration switch). Shortfalls are reported as revolver need, not hidden."""
    if interest_basis not in ("beginning", "average"):
        raise ValueError("interest_basis must be 'beginning' or 'average'")
    bal = {t["name"]: float(t["balance"]) for t in tranches}
    orig = dict(bal)
    cash = opening_cash
    periods = []
    for t_idx, cfads in enumerate(cash_available):
        begin = dict(bal)
        end_guess = dict(begin)
        for _ in range(max_iter if interest_basis == "average" else 1):
            interest, pik_add, mand, sweep = {}, {}, {}, {}
            for tr in tranches:
                n = tr["name"]
                base = begin[n] if interest_basis == "beginning" else (begin[n] + end_guess[n]) / 2.0
                i_amt = base * tr["rate"]
                interest[n] = 0.0 if tr.get("pik") else i_amt
                pik_add[n] = i_amt if tr.get("pik") else 0.0
                mand[n] = min(begin[n], orig[n] * tr.get("amort", 0.0))
            excess = cash + cfads - sum(interest.values()) - sum(mand.values()) - min_cash
            remaining = max(excess, 0.0)
            new_end = {}
            for tr in tranches:
                n = tr["name"]
                after_mand = begin[n] - mand[n] + pik_add[n]
                pay = min(after_mand, remaining) if tr.get("sweep") else 0.0
                sweep[n] = pay
                remaining -= pay
                new_end[n] = after_mand - pay
            if interest_basis == "beginning" or all(abs(new_end[k] - end_guess[k]) < 1e-9 for k in new_end):
                end_guess = new_end
                break
            end_guess = new_end
        bal = end_guess
        shortfall = -excess if excess < 0 else 0.0
        # Unswept excess stays on the balance sheet; a shortfall is drawn on the revolver
        # (reported, not added to any tranche) so cash ends at the minimum.
        cash = min_cash + remaining if excess >= 0 else min_cash
        periods.append({"period": t_idx + 1, "begin": begin, "cash_interest": interest, "pik_accrued": pik_add,
                        "mandatory": mand, "sweep": sweep, "end": dict(bal), "ending_cash": cash,
                        "revolver_need": shortfall})
    return {"periods": periods, "ending_balances": bal}


# ---------------------------------------------------------------- CLI

PUBLIC = [capm, unlever_beta, relever_beta, cash_corrected_beta, after_tax_cost_of_debt, wacc,
          discount_exponents, discount_factors, present_value, unlevered_fcf, gordon_terminal_value,
          exit_multiple_terminal_value, terminal_exponent, terminal_checks, equity_bridge,
          treasury_stock_shares, diluted_value_per_share, moic, npv, irr, xirr, sources_and_uses,
          exit_equity, interest_limit_163j, debt_schedule]


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    funcs = {f.__name__: f for f in PUBLIC}
    if not argv or argv[0] in ("-h", "--help", "list"):
        for f in PUBLIC:
            doc = (inspect.getdoc(f) or "").splitlines()
            print(f"{f.__name__}{inspect.signature(f)}\n    {doc[0] if doc else ''}")
        return 0
    name = argv[0]
    if name not in funcs:
        print(f"unknown function {name!r}; run 'list'", file=sys.stderr)
        return 2
    raw = argv[1] if len(argv) > 1 else "{}"
    if raw.startswith("@"):
        with open(raw[1:], encoding="utf-8") as fh:
            raw = fh.read()
    kwargs = json.loads(raw)
    try:
        result = funcs[name](**kwargs)
    except (ValueError, RuntimeError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
