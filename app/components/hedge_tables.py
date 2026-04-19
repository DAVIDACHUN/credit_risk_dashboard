"""
Hedge summary table — shows per-sleeve hedge ratio, net CS01, and beta.
"""

import pandas as pd
from dash import dash_table, html
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.styles import BORDER, POS_GREEN, WARN_AMBER, NEG_RED


def hedge_summary_table(hedge_df: pd.DataFrame, latest_date: pd.Timestamp):
    row = hedge_df[hedge_df["date"] == latest_date]
    if row.empty:
        return html.Div("No hedge data.")
    r = row.iloc[0]

    summary = pd.DataFrame([{
        "Instrument":     r["instrument"],
        "Notional ($mm)": f"{r['notional_mm']:.1f}",
        "Hedge CS01":     f"${r['hedge_cs01']:,.0f}",
        "Gross CS01":     f"${r['gross_cs01']:,.0f}",
        "Net CS01":       f"${r['net_cs01']:,.0f}",
        "Hedge Ratio":    f"{r['hedge_ratio']*100:.1f}%",
        "Eff. Beta":      f"{r['effective_beta']:.3f}",
    }])

    return dash_table.DataTable(
        data=summary.to_dict("records"),
        columns=[{"name": c, "id": c} for c in summary.columns],
        style_cell={"fontFamily": "Inter, sans-serif", "fontSize": "12px",
                    "padding": "8px 12px", "border": f"1px solid {BORDER}"},
        style_header={"fontWeight": "700", "backgroundColor": "#F9FAFB",
                      "borderBottom": f"2px solid {BORDER}"},
    )
