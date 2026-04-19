"""
P&L charts:
  - Actual vs Explained P&L (bar + line overlay)
  - Hedged vs Unhedged cumulative P&L
  - Component waterfall for selected date
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.styles import CHART_LAYOUT, POS_GREEN, NEG_RED, PRIMARY, WARN_AMBER


COMPONENT_COLORS = {
    "Carry":    "#54A24B",
    "Spread":   "#4C78A8",
    "Roll":     "#72B7B2",
    "Basis":    "#F58518",
    "Event":    "#C4314B",
    "Residual": "#B279A2",
}


def actual_vs_explained(daily_pnl: pd.DataFrame) -> go.Figure:
    """Bar chart: actual P&L bars, explained P&L line overlay."""
    colors = [POS_GREEN if v >= 0 else NEG_RED for v in daily_pnl["actual_pnl"]]

    fig = go.Figure()
    fig.add_bar(
        x=daily_pnl["date"], y=daily_pnl["actual_pnl"],
        name="Actual P&L", marker_color=colors, opacity=0.85,
    )
    fig.add_scatter(
        x=daily_pnl["date"], y=daily_pnl["explained_pnl"],
        mode="lines", name="Explained P&L",
        line=dict(color=PRIMARY, width=2, dash="dot"),
    )
    fig.update_layout(
        **CHART_LAYOUT,
        title="Actual vs Explained P&L",
        yaxis_title="USD",
        hovermode="x unified",
    )
    return fig


def hedged_vs_unhedged(efficiency_df: pd.DataFrame) -> go.Figure:
    """Cumulative P&L: gross (unhedged) vs net (hedged)."""
    fig = go.Figure()
    fig.add_scatter(
        x=efficiency_df["date"], y=efficiency_df["cumulative_gross"],
        name="Unhedged", line=dict(color=NEG_RED, width=2),
        fill="tozeroy", fillcolor="rgba(196,49,75,0.08)",
    )
    fig.add_scatter(
        x=efficiency_df["date"], y=efficiency_df["cumulative_net"],
        name="Hedged", line=dict(color=POS_GREEN, width=2.5),
    )
    fig.update_layout(
        **CHART_LAYOUT,
        title="Hedged vs Unhedged Cumulative P&L",
        yaxis_title="USD (cumulative)",
        hovermode="x unified",
    )
    return fig


def component_waterfall(daily_pnl: pd.DataFrame, date: pd.Timestamp) -> go.Figure:
    """Stacked bar waterfall of P&L components for a single date."""
    from analytics.pnl_decomposition import LABEL_MAP, COMPONENTS
    row = daily_pnl[daily_pnl["date"] == date]
    if row.empty:
        return go.Figure()
    row = row.iloc[0]

    labels = [LABEL_MAP[c] for c in COMPONENTS]
    values = [row[c] for c in COMPONENTS]
    colors = [COMPONENT_COLORS.get(l, "#999") for l in labels]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        text=[f"${v:,.0f}" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title=f"P&L Components — {pd.Timestamp(date).strftime('%d %b %Y')}",
        yaxis_title="USD",
        showlegend=False,
    )
    return fig
