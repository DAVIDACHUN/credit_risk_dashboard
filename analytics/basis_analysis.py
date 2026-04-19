"""
Bond-CDS basis analytics.

Basis = bond spread - CDS spread (negative = cash bonds cheaper than CDS).

Key risk: as basis drifts negative (cash cheapens vs CDS), index hedges
(referencing CDS) over-hedge the cash book, creating basis P&L drag.
In the software / private-credit sector this is the primary source of
residual P&L through early 2026.
"""

from __future__ import annotations
from typing import Optional
import pandas as pd
import numpy as np
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "thresholds.yaml"


def load_thresholds() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)["basis"]


def basis_summary(basis_df: pd.DataFrame, date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """
    Summary of basis by issuer for a given date (or latest).
    Flags issuers breaching warning / breach thresholds.
    """
    thresh = load_thresholds()
    df = basis_df.copy()
    if date:
        df = df[df["date"] == date]
    else:
        df = df[df["date"] == df["date"].max()]

    df = df[["issuer", "sector", "bond_spread_bps", "cds_spread_bps", "basis_bps"]].copy()
    df["status"] = "OK"
    df.loc[df["basis_bps"] < thresh["basis_warn_bps"],   "status"] = "WARN"
    df.loc[df["basis_bps"] < thresh["basis_breach_bps"], "status"] = "BREACH"
    return df.sort_values("basis_bps")


def sector_basis(basis_df: pd.DataFrame) -> pd.DataFrame:
    """Average basis by sector over time."""
    return (
        basis_df.groupby(["date", "sector"])["basis_bps"]
        .mean()
        .reset_index()
        .rename(columns={"basis_bps": "avg_basis_bps"})
    )


def basis_alerts(basis_df: pd.DataFrame) -> pd.DataFrame:
    """
    Return all date-issuer pairs where basis breached a threshold,
    with daily basis move flagged separately.
    """
    thresh = load_thresholds()
    df = basis_df.sort_values(["issuer", "date"]).copy()
    df["basis_change"] = df.groupby("issuer")["basis_bps"].diff()

    alerts = []
    breaches = df[df["basis_bps"] < thresh["basis_breach_bps"]]
    for _, row in breaches.iterrows():
        alerts.append({
            "date": row["date"], "issuer": row["issuer"],
            "sector": row["sector"], "basis_bps": row["basis_bps"],
            "type": "BREACH", "detail": f"Basis {row['basis_bps']:.0f}bps < {thresh['basis_breach_bps']}bps threshold",
        })

    moves = df[df["basis_change"].abs() > thresh["basis_change_warn"]]
    for _, row in moves.iterrows():
        alerts.append({
            "date": row["date"], "issuer": row["issuer"],
            "sector": row["sector"], "basis_bps": row["basis_bps"],
            "type": "MOVE", "detail": f"Daily basis move {row['basis_change']:+.0f}bps",
        })

    out = pd.DataFrame(alerts)
    if not out.empty:
        out = pd.DataFrame(out).sort_values("date", ascending=False)
    else:
        out = pd.DataFrame(out, columns=["date","issuer","sector","basis_bps","type","detail"])
    return out
