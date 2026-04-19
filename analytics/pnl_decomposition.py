"""
P&L decomposition analytics.

Aggregates position-level daily P&L into:
  - Book-level totals by component
  - Explained % = (actual - residual) / |actual|
  - Residual %  = residual / |actual|
  - Cumulative P&L series for charting
"""

from __future__ import annotations
from typing import Optional
import pandas as pd
import numpy as np


COMPONENTS = ["carry_pnl", "spread_pnl", "roll_pnl", "basis_pnl", "event_pnl", "residual_pnl"]
LABEL_MAP  = {
    "carry_pnl":    "Carry",
    "spread_pnl":   "Spread",
    "roll_pnl":     "Roll",
    "basis_pnl":    "Basis",
    "event_pnl":    "Event",
    "residual_pnl": "Residual",
}


def daily_book_pnl(pnl_df: pd.DataFrame, book_id: Optional[str] = None) -> pd.DataFrame:
    """
    Aggregate position-level P&L to book-level daily series.

    Returns DataFrame indexed by date with columns:
        actual_pnl, explained_pnl, carry_pnl, spread_pnl, roll_pnl,
        basis_pnl, event_pnl, residual_pnl,
        explained_pct, residual_pct, cumulative_actual, cumulative_explained
    """
    df = pnl_df.copy()
    if book_id:
        df = df[df["book_id"] == book_id]

    agg_cols = ["actual_pnl", "explained_pnl"] + COMPONENTS
    daily = (
        df.groupby("date")[agg_cols]
        .sum()
        .sort_index()
        .reset_index()
    )

    # Explained / residual ratios (avoid div-by-zero)
    abs_actual = daily["actual_pnl"].abs().replace(0, np.nan)
    daily["explained_pct"] = (daily["explained_pnl"] / abs_actual).clip(-2, 2)
    daily["residual_pct"]  = (daily["residual_pnl"]  / abs_actual).clip(-2, 2)

    daily["cumulative_actual"]    = daily["actual_pnl"].cumsum()
    daily["cumulative_explained"] = daily["explained_pnl"].cumsum()

    return daily


def sector_pnl(pnl_df: pd.DataFrame, book_id: Optional[str] = None) -> pd.DataFrame:
    """Aggregate daily P&L by sector."""
    df = pnl_df.copy()
    if book_id:
        df = df[df["book_id"] == book_id]
    return (
        df.groupby(["date", "sector"])[["actual_pnl", "spread_pnl", "carry_pnl"]]
        .sum()
        .reset_index()
    )


def pnl_waterfall(daily_pnl: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
    """
    Return waterfall decomposition for a single date:
    Carry → Spread → Roll → Basis → Event → Residual → Actual.
    """
    row = daily_pnl[daily_pnl["date"] == date]
    if row.empty:
        return pd.DataFrame()

    row = row.iloc[0]
    records = [{"component": LABEL_MAP[c], "value": row[c]} for c in COMPONENTS]
    records.append({"component": "Actual P&L", "value": row["actual_pnl"]})
    return pd.DataFrame(records)


def top_movers(pnl_df: pd.DataFrame, date: pd.Timestamp, n: int = 3) -> pd.DataFrame:
    """Return top-n P&L movers (by absolute actual P&L) for a given date."""
    day = pnl_df[pnl_df["date"] == date].copy()
    if day.empty:
        return pd.DataFrame()
    day["abs_pnl"] = day["actual_pnl"].abs()
    return (
        day.nlargest(n, "abs_pnl")[["issuer", "sector", "actual_pnl", "spread_pnl", "event_pnl"]]
        .reset_index(drop=True)
    )
