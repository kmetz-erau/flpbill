"""
FPL business rate constants and rate-fit screening logic.

Source: FPL "Business rates and clauses, Effective January 2026"
(bus-eff-jan-2026.pdf), FL PSC Docket 20250011-EI et al.

Price components verified against the Jan-2026 rate insert; the GS-1/GSD-1
eligibility boundary verified against FPL Electric Tariff Section 8 (Sheets
8.101 / 8.105). The tariff prevails over the rate insert, so re-confirm when
rates change -- these constants are the single place to update.
"""

# ---- GS-1 (General Service Non-Demand) -----------------------------------
GS1_BASE        = 14.20        # $/month
GS1_ENERGY      = 0.12662      # $/kWh  = (8.039+0.144+0.050+0.331+0.927+3.202-0.031)c
GS1_MIN_BILL    = 30.00        # $/month minimum base bill (metered GS-1/GST-1)
# Eligibility boundary, confirmed against FPL Electric Tariff Section 8:
#   GS-1  General Service Non-Demand  = 0-20 kW   (Sheet 8.101)
#   GSD-1 General Service Demand      = 21-499 kW (Sheet 8.105; "in excess of
#         20 kW and less than 500 kW"). GS-1's ceiling is therefore 20 kW.
# (The "25 kW" on the rate insert is the floor for the optional HLFT/SDTR
#  demand-TOU riders, not the GS-1/GSD-1 boundary.)
GS1_DEMAND_CAP  = 20.0         # kW -- top of the GS-1 range

# ---- GSD-1 (General Service Demand) --------------------------------------
GSD1_BASE       = 33.71        # $/month
GSD1_DEMAND     = 15.03        # $/kW   = 12.70+0.49+0.16+1.80-0.12
GSD1_ENERGY     = 0.06312      # $/kWh  = (2.825+0.286+3.201)c

HOURS_PER_MONTH = 730.0
BREAKEVEN_LOAD_FACTOR = 0.324  # above -> GSD-1 wins; below -> GS-1 wins

# Rate classes that are time-of-use: rate-swap math below does not apply;
# these are load-shift / operational reviews.
TOU_RATES = {"GSDT-1", "GSLDT-1", "GSLDT-2", "GSLDT-3", "GST-1",
             "SDTR-1A", "SDTR-1B", "CST-1", "CST-2"}
LIGHTING_RATES = {"OL-1", "SL-1", "LT-1", "SL-2", "PL-1", "OS-2"}


def min_demand_kw(kwh, days=None):
    """Lowest demand the meter could have pulled: kWh / hours in period."""
    if kwh is None:
        return None
    hours = days * 24 if days else HOURS_PER_MONTH
    return kwh / hours


def load_factor(kwh, peak_kw, days=None):
    """kWh / (peak kW * hours). None if peak unknown."""
    if kwh is None or not peak_kw:
        return None
    hours = days * 24 if days else HOURS_PER_MONTH
    return kwh / (peak_kw * hours)


def gs1_cost(kwh):
    if kwh is None:
        return None
    return max(GS1_BASE + GS1_ENERGY * kwh, GS1_MIN_BILL)


def gsd1_cost(kwh, peak_kw):
    """Uses actual peak if given, else the min-demand floor (GSD-1 best case)."""
    if kwh is None:
        return None
    demand = peak_kw if peak_kw else min_demand_kw(kwh)
    return GSD1_BASE + GSD1_DEMAND * demand + GSD1_ENERGY * kwh


def breakeven_peak_kw(kwh):
    """Peak kW at which GS-1 and GSD-1 cost the same for this kWh.
    Actual peak below this -> GSD-1 cheaper; above -> GS-1 cheaper."""
    if kwh is None:
        return None
    return (GS1_BASE - GSD1_BASE + (GS1_ENERGY - GSD1_ENERGY) * kwh) / GSD1_DEMAND


def screen(rate, kwh, peak_kw=None, days=None):
    """Return a dict of derived metrics + a plain-language flag for one bill."""
    rate = (rate or "").upper().strip()
    out = {
        "min_demand_kw": None, "load_factor": None,
        "est_gs1": None, "est_gsd1": None,
        "breakeven_peak_kw": None, "recommended_rate": None, "flag": "",
    }
    if kwh is None:
        out["flag"] = "no consumption parsed"
        return out

    out["min_demand_kw"] = round(min_demand_kw(kwh, days), 1)

    if rate in TOU_RATES or rate in LIGHTING_RATES:
        out["flag"] = f"{rate}: TOU/lighting - load-shift/operational review, not a rate swap"
        return out

    if rate not in ("GS-1", "GSD-1", "GS-1EV", "GSD-1EV"):
        out["flag"] = f"{rate or 'unknown rate'}: outside GS-1/GSD-1 screen"
        return out

    be = breakeven_peak_kw(kwh)
    out["breakeven_peak_kw"] = round(be, 1)
    out["est_gs1"] = round(gs1_cost(kwh), 2)
    out["est_gsd1"] = round(gsd1_cost(kwh, peak_kw), 2)

    # misclassification: a GS-1 account whose demand clears the eligibility
    # ceiling cannot legitimately sit on GS-1. Use billed/actual peak when we
    # have it; otherwise fall back to the min-demand floor (kWh / hours), which
    # is the demand the account *must* have exceeded.
    md = min_demand_kw(kwh, days)
    demand_used = peak_kw if peak_kw else md
    if rate.startswith("GS-1") and demand_used > GS1_DEMAND_CAP:
        out["recommended_rate"] = "GSD-1 (or GSLD-1)"
        basis = "billed demand" if peak_kw else "min demand"
        out["flag"] = (f"MISCLASSIFIED: {basis} {demand_used:.0f} kW > "
                       f"{GS1_DEMAND_CAP:.0f} kW GS-1 ceiling - move to a demand rate")
        return out

    if peak_kw:
        out["load_factor"] = round(load_factor(kwh, peak_kw, days), 3)
        cheaper = "GS-1" if out["est_gs1"] <= out["est_gsd1"] else "GSD-1"
        out["recommended_rate"] = cheaper
        delta = abs(out["est_gs1"] - out["est_gsd1"])
        out["flag"] = f"{cheaper} cheaper by ${delta:,.0f}/mo"
    else:
        out["flag"] = f"enter peak kW to decide (breakeven at {be:.1f} kW)"
    return out
