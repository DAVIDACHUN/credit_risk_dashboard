"""
Generate realistic sample data for the credit risk dashboard.

Narrative:  HY credit book skewed toward lower-rated software and
private-credit-adjacent leveraged loan borrowers, consistent with the
Reuters (Feb 2026) observation that AI-disruption risk is pressuring
B/B- software issuers, and the Fitch finding (April 2026) that private-
credit defaults hit a record 9.2% in 2025.

Spread dynamics reflect:
  - Software / Private Credit: persistent widening + two downgrade events
  - Healthcare / Retail: moderate stress
  - Industrials: mild tightening
  - Energy: elevated volatility

CDX HY 5Y index hedge; position beta drifts over time, widening the gap
between explained and actual P&L in stress sectors.
"""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

OUT = Path(__file__).parent

# ── date range ─────────────────────────────────────────────────────────────
START = pd.Timestamp("2025-10-01")
END   = pd.Timestamp("2026-04-18")
BDAYS = pd.bdate_range(START, END)
N     = len(BDAYS)

# ── portfolio positions ─────────────────────────────────────────────────────
POSITIONS = [
    # Software / SaaS – thesis sector
    {"cusip":"12345A100","issuer":"CloudSoft Inc",    "sector":"Software",       "rating":"B",  "notional_mm":25,"coupon_bps":550,"mat_yrs":5,"init_spread":445},
    {"cusip":"12345B200","issuer":"DataSys Corp",     "sector":"Software",       "rating":"B-", "notional_mm":20,"coupon_bps":600,"mat_yrs":4,"init_spread":520},
    {"cusip":"12345C300","issuer":"AppWorks LLC",     "sector":"Software",       "rating":"B",  "notional_mm":15,"coupon_bps":575,"mat_yrs":5,"init_spread":465},
    {"cusip":"12345D400","issuer":"TechServices Inc", "sector":"Software",       "rating":"B+", "notional_mm":20,"coupon_bps":500,"mat_yrs":6,"init_spread":390},
    {"cusip":"12345E500","issuer":"CloudInfra LLC",   "sector":"Software",       "rating":"B",  "notional_mm":18,"coupon_bps":560,"mat_yrs":4,"init_spread":430},
    # Healthcare
    {"cusip":"23456A100","issuer":"MedTech Partners", "sector":"Healthcare",     "rating":"BB-","notional_mm":30,"coupon_bps":425,"mat_yrs":7,"init_spread":285},
    {"cusip":"23456B200","issuer":"CareBridge Health","sector":"Healthcare",     "rating":"B+", "notional_mm":22,"coupon_bps":475,"mat_yrs":5,"init_spread":375},
    # Retail
    {"cusip":"34567A100","issuer":"RetailCo Inc",     "sector":"Retail",         "rating":"B",  "notional_mm":20,"coupon_bps":550,"mat_yrs":4,"init_spread":485},
    {"cusip":"34567B200","issuer":"ShopNet LLC",      "sector":"Retail",         "rating":"B-", "notional_mm":15,"coupon_bps":600,"mat_yrs":3,"init_spread":555},
    # Industrials
    {"cusip":"45678A100","issuer":"IndustrialCo",     "sector":"Industrials",    "rating":"BB", "notional_mm":25,"coupon_bps":375,"mat_yrs":7,"init_spread":225},
    {"cusip":"45678B200","issuer":"ManufactCo",       "sector":"Industrials",    "rating":"BB+","notional_mm":20,"coupon_bps":350,"mat_yrs":6,"init_spread":185},
    # Energy
    {"cusip":"56789A100","issuer":"EnergyPipe Corp",  "sector":"Energy",         "rating":"BB-","notional_mm":18,"coupon_bps":450,"mat_yrs":5,"init_spread":315},
    {"cusip":"56789B200","issuer":"MidStreamCo",      "sector":"Energy",         "rating":"BB", "notional_mm":22,"coupon_bps":400,"mat_yrs":6,"init_spread":265},
    # Private Credit Adjacent – highest default risk
    {"cusip":"67890A100","issuer":"PrivateCo Alpha",  "sector":"Private Credit", "rating":"B",  "notional_mm":30,"coupon_bps":650,"mat_yrs":4,"init_spread":625},
    {"cusip":"67890B200","issuer":"PrivateCo Beta",   "sector":"Private Credit", "rating":"B-", "notional_mm":25,"coupon_bps":725,"mat_yrs":3,"init_spread":780},
]

# ── sector spread dynamics ──────────────────────────────────────────────────
# (drift bps/day, mean-reversion speed, daily vol bps, sector beta to CDX)
SECTOR_PARAMS = {
    "Software":       {"drift": 0.55, "kappa": 0.015, "vol": 14.0, "cdx_beta": 1.35},
    "Healthcare":     {"drift": 0.15, "kappa": 0.025, "vol":  9.0, "cdx_beta": 0.85},
    "Retail":         {"drift": 0.35, "kappa": 0.020, "vol": 16.0, "cdx_beta": 1.10},
    "Industrials":    {"drift":-0.10, "kappa": 0.040, "vol":  7.0, "cdx_beta": 0.70},
    "Energy":         {"drift": 0.20, "kappa": 0.025, "vol": 20.0, "cdx_beta": 1.00},
    "Private Credit": {"drift": 0.80, "kappa": 0.010, "vol": 22.0, "cdx_beta": 1.50},
}

# Downgrade events: (cusip, event_date, rating_after, spread_jump_bps)
DOWNGRADE_EVENTS = [
    ("12345B200", pd.Timestamp("2026-01-15"), "CCC+", 320),   # DataSys: B- → CCC+
    ("34567B200", pd.Timestamp("2026-02-20"), "CCC+", 275),   # ShopNet: B- → CCC+
]
DOWNGRADE_MAP = {(e[0], e[1]): e for e in DOWNGRADE_EVENTS}

# ── CDX HY 5Y index spread ──────────────────────────────────────────────────
cdx_init   = 335.0
cdx_drift  = 0.25          # mild widening trend
cdx_vol    = 11.0
cdx_kappa  = 0.020

def ou_path(init, drift, kappa, vol, n, systematic_shocks):
    """Ornstein-Uhlenbeck spread path with systematic + idiosyncratic noise."""
    s = np.zeros(n)
    s[0] = init
    idio = np.random.normal(0, vol, n)
    for t in range(1, n):
        ds = drift + kappa * (init - s[t-1]) + 0.7 * systematic_shocks[t] + 0.3 * idio[t]
        s[t] = max(s[t-1] + ds, 10.0)   # floor at 10bps
    return s

# Systematic credit factor (drives correlation across sectors)
sys_shock = np.random.normal(0, 8.0, N)

cdx_spreads = ou_path(cdx_init, cdx_drift, cdx_kappa, cdx_vol, N, sys_shock)

# ── CS01 helper ─────────────────────────────────────────────────────────────
def cs01(notional_mm, mat_yrs):
    """Dollar CS01 ≈ notional × modified duration / 10 000."""
    dur = mat_yrs * 0.85
    return notional_mm * 1_000_000 * dur / 10_000

# ── build position-level spread & P&L series ───────────────────────────────
position_records  = []
pnl_records       = []
basis_records     = []

for pos in POSITIONS:
    sp = SECTOR_PARAMS[pos["sector"]]
    cusip = pos["cusip"]
    rating_current = pos["rating"]

    # generate bond spread path
    issuer_spreads = ou_path(
        pos["init_spread"], sp["drift"], sp["kappa"], sp["vol"], N,
        sys_shock * sp["cdx_beta"]
    )

    # CDS spread path: bond-CDS basis starts at –20bps, drifts negative for stress sectors
    basis_drift = -0.08 if pos["sector"] in ("Software","Private Credit","Retail") else -0.02
    cds_spreads = issuer_spreads.copy()
    basis_path  = np.zeros(N)
    basis_path[0] = -20.0
    for t in range(1, N):
        basis_path[t] = basis_path[t-1] + basis_drift + np.random.normal(0, 2.5)
        cds_spreads[t] = max(issuer_spreads[t] - basis_path[t], 5.0)

    c01 = cs01(pos["notional_mm"], pos["mat_yrs"])
    notional = pos["notional_mm"] * 1_000_000
    daily_carry = notional * pos["coupon_bps"] / 10_000 / 252
    roll_down   = 0.35   # bps/day

    for t, dt in enumerate(BDAYS):
        # handle downgrade events
        key = (cusip, dt)
        if key in DOWNGRADE_MAP:
            _, _, rating_current, jump = DOWNGRADE_MAP[key]
            issuer_spreads[t] += jump

        s_prev = issuer_spreads[t-1] if t > 0 else issuer_spreads[0]
        d_spread = issuer_spreads[t] - s_prev

        carry_pnl  = daily_carry
        spread_pnl = -c01 * d_spread
        roll_pnl   = c01 * roll_down
        basis_pnl  = -(basis_path[t] - (basis_path[t-1] if t>0 else basis_path[0])) * c01 * 0.1
        event_pnl  = -c01 * (DOWNGRADE_MAP[key][3] if key in DOWNGRADE_MAP else 0)
        residual   = np.random.normal(0, abs(spread_pnl) * 0.06 + 200)

        actual_pnl    = carry_pnl + spread_pnl + roll_pnl + basis_pnl + event_pnl + residual
        explained_pnl = carry_pnl + spread_pnl + roll_pnl + basis_pnl + event_pnl

        pnl_records.append({
            "date": dt, "book_id": "HY-CREDIT-01", "cusip": cusip,
            "issuer": pos["issuer"], "sector": pos["sector"],
            "actual_pnl": actual_pnl, "explained_pnl": explained_pnl,
            "carry_pnl": carry_pnl, "spread_pnl": spread_pnl,
            "roll_pnl": roll_pnl, "basis_pnl": basis_pnl,
            "event_pnl": event_pnl, "residual_pnl": residual,
        })

        basis_records.append({
            "date": dt, "cusip": cusip, "issuer": pos["issuer"],
            "sector": pos["sector"],
            "bond_spread_bps": round(issuer_spreads[t], 2),
            "cds_spread_bps":  round(cds_spreads[t], 2),
            "basis_bps":       round(basis_path[t], 2),
        })

        if t == 0:
            position_records.append({
                "cusip": cusip, "issuer": pos["issuer"],
                "sector": pos["sector"], "rating": rating_current,
                "notional_mm": pos["notional_mm"],
                "coupon_bps": pos["coupon_bps"], "mat_yrs": pos["mat_yrs"],
                "cs01_usd": round(c01, 0),
                "init_spread_bps": pos["init_spread"],
            })

    # update rating after events
    for ev in DOWNGRADE_EVENTS:
        if ev[0] == cusip:
            for pr in position_records:
                if pr["cusip"] == cusip:
                    pr["rating_current"] = ev[2]

# ── CDX hedge records ───────────────────────────────────────────────────────
hedge_records = []
# CDX HY notional: sized to hedge ~85% of gross CS01 at inception
gross_cs01 = sum(cs01(p["notional_mm"], p["mat_yrs"]) for p in POSITIONS)
cdx_cs01_per_mm = cs01(1, 5)
cdx_notional_mm = (gross_cs01 * 0.85) / cdx_cs01_per_mm

cdx_prev = cdx_spreads[0]
for t, dt in enumerate(BDAYS):
    # beta drift: hedge becomes less effective as software names widen faster
    effective_beta = 1.0 + 0.0015 * t
    hedge_cs01 = -cdx_notional_mm * cdx_cs01_per_mm    # negative = short risk
    cdx_d = cdx_spreads[t] - cdx_prev
    hedge_pnl = -hedge_cs01 * cdx_d   # gain when spreads widen (protection bought)

    hedge_records.append({
        "date": dt, "book_id": "HY-CREDIT-01",
        "instrument": "CDX.NA.HY.5Y",
        "notional_mm": round(cdx_notional_mm, 1),
        "hedge_cs01": round(hedge_cs01, 0),
        "gross_cs01": round(gross_cs01, 0),
        "net_cs01":   round(gross_cs01 + hedge_cs01, 0),
        "hedge_ratio": round(-hedge_cs01 / gross_cs01, 4),
        "effective_beta": round(effective_beta, 4),
        "cdx_spread_bps": round(cdx_spreads[t], 2),
        "hedge_pnl": round(hedge_pnl, 2),
    })
    cdx_prev = cdx_spreads[t]

# ── write CSVs ──────────────────────────────────────────────────────────────
pd.DataFrame(position_records).to_csv(OUT / "positions.csv",   index=False)
pd.DataFrame(pnl_records).to_csv(     OUT / "pnl_daily.csv",   index=False)
pd.DataFrame(basis_records).to_csv(   OUT / "basis_data.csv",  index=False)
pd.DataFrame(hedge_records).to_csv(   OUT / "hedge_data.csv",  index=False)

print(f"Generated {N} business days from {START.date()} to {END.date()}")
print(f"  positions.csv  : {len(position_records)} rows")
print(f"  pnl_daily.csv  : {len(pnl_records)} rows")
print(f"  basis_data.csv : {len(basis_records)} rows")
print(f"  hedge_data.csv : {len(hedge_records)} rows")
