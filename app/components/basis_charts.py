"""
Basis charts:
  - Bond-CDS basis time series by sector (middle-left panel)
  - Sector hedge ratio bar chart (bottom-right panel)
"""

import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.styles import CHART_LAYOUT, SECTOR_COLORS, WARN_AMBER, NEG_RED, POS_GREEN


def basis_time_series(basis_df: pd.DataFrame, sectors: list[str] | None = None) -> go.Figure:
    """
    Average bond-CDS basis per sector over time.
    Horizontal lines at -50bps (warn) and -100bps (breach).
    """
    from analytics.basis_analysis import sector_basis
    sb = sector_basis(basis_df)

    if sectors:
        sb = sb[sb["sector"].isin(sectors)]

    fig = go.Figure()
    for sector, grp in sb.groupby("sector"):
        fig.add_scatter(
            x=grp["date"], y=grp["avg_basis_bps"],
            name=sector, mode="lines",
            line=dict(color=SECTOR_COLORS.get(sector, "#999"), width=2),
        )

    # threshold lines
    fig.add_hline(y=-50,  line_dash="dot", line_color=WARN_AMBER,
                  annotation_text="Warn –50bps", annotation_position="bottom right")
    fig.add_hline(y=-100, line_dash="dash", line_color=NEG_RED,
                  annotation_text="Breach –100bps", annotation_position="bottom right")

    fig.update_layout(
        **CHART_LAYOUT,
        title="Bond–CDS Basis by Sector",
        yaxis_title="Basis (bps)",
        hovermode="x unified",
    )
    return fig


def sector_hedge_ratio_chart(hedge_df: pd.DataFrame, pnl_df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart: hedge ratio by sector.
    Green if ≥80%, amber if 60–80%, red if <60%.
    """
    from analytics.hedge_efficiency import sector_hedge_ratio
    sr = sector_hedge_ratio(pnl_df, hedge_df)

    colors = []
    for r in sr["hedge_ratio"]:
        if r >= 0.80:
            colors.append(POS_GREEN)
        elif r >= 0.60:
            colors.append(WARN_AMBER)
        else:
            colors.append(NEG_RED)

    fig = go.Figure(go.Bar(
        x=sr["hedge_ratio"] * 100,
        y=sr["sector"],
        orientation="h",
        marker_color=colors,
        text=[f"{r*100:.0f}%" for r in sr["hedge_ratio"]],
        textposition="inside",
    ))
    fig.add_vline(x=80, line_dash="dot", line_color=WARN_AMBER,
                  annotation_text="80% target")
    fig.update_layout(
        **CHART_LAYOUT,
        title="Hedge Ratio by Sector",
        xaxis_title="Hedge Ratio (%)",
        xaxis=dict(range=[0, 105], showgrid=True, gridcolor="#E5E7EB"),
        showlegend=False,
    )
    return fig
