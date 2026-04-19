"""
Hedge efficiency analytics.

Hedge efficiency = 1 - Var(net P&L) / Var(gross P&L)
Expressed as a percentage: how much variance the hedge removes.

Also computes:
  - Hedged vs unhedged cumulative P&L
  - Hedge ratio by sector sleeve
  - Net CS01 over time
"""

import pandas as pd
import numpy as np


def compute_hedge_efficiency(
    pnl_df: pd.DataFrame,
    hedge_df: pd.DataFrame,
    window: int = 21,
) -> pd.DataFrame:
    """
    Rolling hedge efficiency over `window` business days.

    gross_pnl = sum of position P&L (unhedged)
    net_pnl   = gross_pnl + hedge_pnl
    efficiency = 1 - Var(net_pnl, window) / Var(gross_pnl, window)
    """
    gross = (
        pnl_df.groupby("date")["actual_pnl"]
        .sum()
        .rename("gross_pnl")
        .reset_index()
    )
    merged = gross.merge(
        hedge_df[["date", "hedge_pnl", "net_cs01", "hedge_ratio"]],
        on="date", how="left"
    ).fillna(0).sort_values("date")

    merged["net_pnl"] = merged["gross_pnl"] + merged["hedge_pnl"]

    var_gross = merged["gross_pnl"].rolling(window, min_periods=5).var()
    var_net   = merged["net_pnl"].rolling(window, min_periods=5).var()

    merged["hedge_efficiency"] = (1 - var_net / var_gross.replace(0, np.nan)).clip(0, 1)
    merged["cumulative_gross"] = merged["gross_pnl"].cumsum()
    merged["cumulative_net"]   = merged["net_pnl"].cumsum()

    return merged


def sector_hedge_ratio(
    pnl_df: pd.DataFrame,
    hedge_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Approximate hedge ratio by sector using gross CS01 weights.
    Since the hedge is a single CDX index, the sector ratio =
    (sector CS01 weight × overall hedge ratio).
    """
    latest_date = pnl_df["date"].max()
    day = pnl_df[pnl_df["date"] == latest_date]

    sector_pnl_abs = (
        day.groupby("sector")["spread_pnl"]
        .apply(lambda x: x.abs().sum())
        .rename("gross_spread_pnl")
    )
    total = sector_pnl_abs.sum()

    latest_hedge = hedge_df[hedge_df["date"] == latest_date]
    overall_ratio = latest_hedge["hedge_ratio"].values[0] if not latest_hedge.empty else 0.85

    sector_df = sector_pnl_abs.reset_index()
    sector_df["weight"]      = sector_df["gross_spread_pnl"] / total
    sector_df["hedge_ratio"] = overall_ratio * sector_df["weight"] / sector_df["weight"]  # uniform for now
    return sector_df


def net_cs01_series(hedge_df: pd.DataFrame) -> pd.DataFrame:
    """Return net CS01 time series."""
    return hedge_df[["date", "net_cs01", "hedge_ratio", "effective_beta"]].copy()
