"""
Top-row KPI tiles:
  Actual P&L | Explained % | Residual % | Hedge Efficiency % | Net CS01
"""

from dash import html
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.styles import (
    CARD_STYLE, KPI_VALUE_STYLE, KPI_LABEL_STYLE,
    POS_GREEN, NEG_RED, WARN_AMBER, PRIMARY, TEXT_DARK
)


def _fmt_pnl(v):
    sign = "+" if v >= 0 else ""
    if abs(v) >= 1_000_000:
        return f"{sign}${v/1_000_000:.2f}M"
    return f"{sign}${v/1_000:,.0f}K"


def _color_pnl(v):
    return POS_GREEN if v >= 0 else NEG_RED


def _color_pct(v, warn=0.15, breach=0.25):
    if abs(v) >= breach:
        return NEG_RED
    if abs(v) >= warn:
        return WARN_AMBER
    return POS_GREEN


def _color_efficiency(v, warn=0.70, breach=0.50):
    if v < breach:
        return NEG_RED
    if v < warn:
        return WARN_AMBER
    return POS_GREEN


def _color_cs01(v, warn=50_000, breach=100_000):
    if abs(v) >= breach:
        return NEG_RED
    if abs(v) >= warn:
        return WARN_AMBER
    return POS_GREEN


def kpi_card(label, value_str, color=TEXT_DARK, delta=None):
    children = [
        html.Div(label, style=KPI_LABEL_STYLE),
        html.Div(value_str, style={**KPI_VALUE_STYLE, "color": color}),
    ]
    if delta is not None:
        children.append(html.Div(delta, style={"fontSize": "11px", "color": color, "marginTop": "2px"}))
    return html.Div(children, style={**CARD_STYLE, "minWidth": "140px", "flex": "1"})


def build_kpi_row(daily_pnl, hedge_row):
    """
    daily_pnl : one-row Series (latest date from daily_book_pnl)
    hedge_row : one-row Series (latest date from hedge_data)
    """
    actual       = daily_pnl["actual_pnl"]
    explained_p  = daily_pnl.get("explained_pct", 0)
    residual_p   = daily_pnl.get("residual_pct",  0)
    efficiency   = hedge_row.get("hedge_efficiency", 0) if hedge_row is not None else 0
    net_cs01     = hedge_row.get("net_cs01", 0)         if hedge_row is not None else 0

    return html.Div([
        kpi_card("Actual P&L",       _fmt_pnl(actual),
                 color=_color_pnl(actual)),
        kpi_card("Explained",        f"{explained_p*100:.1f}%",
                 color=_color_pct(1 - explained_p)),
        kpi_card("Residual",         f"{residual_p*100:.1f}%",
                 color=_color_pct(abs(residual_p))),
        kpi_card("Hedge Efficiency", f"{efficiency*100:.1f}%",
                 color=_color_efficiency(efficiency)),
        kpi_card("Net CS01",         f"${net_cs01:,.0f}",
                 color=_color_cs01(net_cs01)),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "16px"})
