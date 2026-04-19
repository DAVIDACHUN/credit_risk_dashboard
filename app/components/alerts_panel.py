"""
Alerts and exceptions panel — footer row.

Sources:
  - Basis breaches / large daily moves
  - P&L residual > threshold
  - Hedge efficiency < threshold
  - Net CS01 > threshold
"""

import pandas as pd
import yaml
from pathlib import Path
from dash import html, dash_table
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.styles import NEG_RED, WARN_AMBER, POS_GREEN, BORDER, TEXT_DARK, CARD_STYLE

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "thresholds.yaml"


def _load_thresh():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def build_alerts(daily_pnl, hedge_df, basis_df, latest_date):
    thresh = _load_thresh()
    alerts = []

    # 1. P&L residual threshold
    day = daily_pnl[daily_pnl["date"] == latest_date]
    if not day.empty:
        row = day.iloc[0]
        if abs(row.get("residual_pct", 0)) > thresh["pnl"]["residual_pct_breach"]:
            alerts.append({"Type": "BREACH", "Source": "P&L Residual",
                           "Detail": f"Residual {row['residual_pct']*100:.1f}% of gross P&L",
                           "Date": str(latest_date.date())})
        elif abs(row.get("residual_pct", 0)) > thresh["pnl"]["residual_pct_warn"]:
            alerts.append({"Type": "WARN", "Source": "P&L Residual",
                           "Detail": f"Residual {row['residual_pct']*100:.1f}% of gross P&L",
                           "Date": str(latest_date.date())})

    # 2. Hedge efficiency
    h_row = hedge_df[hedge_df["date"] == latest_date]
    if not h_row.empty:
        eff = h_row.iloc[0].get("hedge_efficiency", 1.0)
        if eff is not None:
            if eff < thresh["hedge"]["efficiency_breach"]:
                alerts.append({"Type": "BREACH", "Source": "Hedge Efficiency",
                               "Detail": f"Efficiency {eff*100:.1f}% < {thresh['hedge']['efficiency_breach']*100:.0f}%",
                               "Date": str(latest_date.date())})
            elif eff < thresh["hedge"]["efficiency_warn"]:
                alerts.append({"Type": "WARN", "Source": "Hedge Efficiency",
                               "Detail": f"Efficiency {eff*100:.1f}% < {thresh['hedge']['efficiency_warn']*100:.0f}%",
                               "Date": str(latest_date.date())})

    # 3. Basis breaches
    from analytics.basis_analysis import basis_alerts
    ba = basis_alerts(basis_df)
    if not ba.empty:
        recent = ba[ba["date"] >= latest_date - pd.Timedelta(days=5)]
        for _, r in recent.head(5).iterrows():
            alerts.append({"Type": r["type"], "Source": f"Basis — {r['issuer']}",
                           "Detail": r["detail"], "Date": str(r["date"].date())})

    df = pd.DataFrame(alerts) if alerts else pd.DataFrame(
        columns=["Type", "Source", "Detail", "Date"])

    return df


def alerts_table(alert_df: pd.DataFrame):
    def row_style(t):
        if t == "BREACH":
            return {"backgroundColor": "#FEF2F2", "color": NEG_RED}
        if t == "WARN":
            return {"backgroundColor": "#FFFBEB", "color": "#92400E"}
        return {}

    if alert_df.empty:
        return html.Div("No open exceptions.", style={"color": POS_GREEN, "fontWeight": "600"})

    return dash_table.DataTable(
        data=alert_df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in alert_df.columns],
        style_cell={"fontFamily": "Inter, sans-serif", "fontSize": "12px",
                    "textAlign": "left", "padding": "6px 10px", "border": f"1px solid {BORDER}"},
        style_header={"fontWeight": "700", "backgroundColor": "#F9FAFB",
                      "borderBottom": f"2px solid {BORDER}"},
        style_data_conditional=[
            {"if": {"filter_query": '{Type} = "BREACH"'},
             "backgroundColor": "#FEF2F2", "color": NEG_RED, "fontWeight": "600"},
            {"if": {"filter_query": '{Type} = "WARN"'},
             "backgroundColor": "#FFFBEB", "color": "#92400E"},
        ],
        page_size=8,
    )
