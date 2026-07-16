"""Unit tests for the rate screening logic. Offline; no bill files needed."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rates  # noqa: E402


def test_min_demand():
    # 132,612 kWh over 30 days -> ~184 kW minimum
    assert round(rates.min_demand_kw(132612, days=30)) == 184
    # default month (730 hrs) when days unknown
    assert round(rates.min_demand_kw(14600)) == 20


def test_load_factor():
    lf = rates.load_factor(39007, 118.4, days=30)
    assert 0.45 < lf < 0.46


def test_breakeven_direction():
    # below breakeven peak -> GSD-1 cheaper; above -> GS-1 cheaper
    kwh = 20000
    be = rates.breakeven_peak_kw(kwh)
    assert rates.gsd1_cost(kwh, be - 5) < rates.gs1_cost(kwh)
    assert rates.gsd1_cost(kwh, be + 5) > rates.gs1_cost(kwh)


def test_gs1_min_bill_floor():
    # tiny usage is floored at the $30 minimum base bill
    assert rates.gs1_cost(50) == rates.GS1_MIN_BILL


def test_misclassified_gs1_flag():
    s = rates.screen("GS-1", 132612, peak_kw=None, days=30)
    assert "MISCLASSIFIED" in s["flag"]
    assert s["recommended_rate"].startswith("GSD-1")


def test_tou_is_not_a_swap():
    s = rates.screen("GSDT-1", 63560, days=30)
    assert "TOU" in s["flag"]
    assert s["recommended_rate"] is None


def test_gsd1_with_peak_picks_cheaper():
    # high load factor -> GSD-1 should win
    s = rates.screen("GSD-1", 39007, peak_kw=118.4, days=30)
    assert s["recommended_rate"] in ("GS-1", "GSD-1")
    assert s["load_factor"] > 0.32
    assert s["recommended_rate"] == "GSD-1"


def test_no_consumption():
    s = rates.screen("GS-1", None)
    assert s["flag"] == "no consumption parsed"
