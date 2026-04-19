"""
Single-screen dashboard layout.

┌─────────────────────────────────────────────────────────────────┐
│  Header: title + date/book dropdowns + Export PDF button        │
├──────────┬──────────┬──────────┬──────────┬───────────────────-─┤
│ Actual   │ Explained│ Residual │ Hedge    │ Net CS01            │  ← KPI tiles
│ P&L      │    %     │    %     │ Eff. %   │                     │
├───────────────────────────┬─────────────────────────────────────┤
│ Actual vs Explained P&L   │ Hedged vs Unhedged cumulative P&L   │
├───────────────────────────┼─────────────────────────────────────┤
│ Basis time series         │ Sector hedge ratio                  │
├─────────────────────────────────────────────────────────────────┤
│ Open exceptions / alerts table                                  │
└─────────────────────────────────────────────────────────────────┘
"""

from dash import html, dcc
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.styles import BG, CARD_STYLE, PRIMARY, TEXT_DARK, FONT_FAMILY, BORDER


def build_layout(dates: list[str], books: list[str]) -> html.Div:
    header = html.Div([
        html.Div([
            html.Div("Credit Risk Dashboard", style={
                "fontSize": "18px", "fontWeight": "700",
                "color": TEXT_DARK, "fontFamily": FONT_FAMILY,
            }),
            html.Div("P&L Attribution · Hedge Efficiency · Basis Monitor", style={
                "fontSize": "11px", "color": "#6B7280", "fontFamily": FONT_FAMILY,
            }),
        ]),
        html.Div([
            dcc.Dropdown(
                id="book-dropdown",
                options=[{"label": b, "value": b} for b in books],
                value=books[0] if books else None,
                clearable=False,
                style={"width": "200px", "fontSize": "12px"},
            ),
            dcc.Dropdown(
                id="date-dropdown",
                options=[{"label": d, "value": d} for d in dates],
                value=dates[-1] if dates else None,
                clearable=False,
                style={"width": "160px", "fontSize": "12px"},
            ),
            html.Button(
                "Export PDF", id="export-btn", n_clicks=0,
                style={
                    "backgroundColor": PRIMARY, "color": "white",
                    "border": "none", "borderRadius": "6px",
                    "padding": "8px 16px", "cursor": "pointer",
                    "fontSize": "12px", "fontWeight": "600",
                    "fontFamily": FONT_FAMILY,
                }
            ),
            dcc.Download(id="pdf-download"),
        ], style={"display": "flex", "gap": "10px", "alignItems": "center"}),
    ], style={
        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
        "padding": "14px 20px", "background": "white",
        "borderBottom": f"1px solid {BORDER}", "marginBottom": "16px",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.06)",
    })

    kpi_row = html.Div(id="kpi-row")

    charts_mid = html.Div([
        html.Div([dcc.Graph(id="pnl-chart",   config={"displayModeBar": False})],
                 style={**CARD_STYLE, "flex": "1"}),
        html.Div([dcc.Graph(id="hedge-chart", config={"displayModeBar": False})],
                 style={**CARD_STYLE, "flex": "1"}),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"})

    charts_bot = html.Div([
        html.Div([dcc.Graph(id="basis-chart",  config={"displayModeBar": False})],
                 style={**CARD_STYLE, "flex": "1"}),
        html.Div([dcc.Graph(id="sector-chart", config={"displayModeBar": False})],
                 style={**CARD_STYLE, "flex": "1"}),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"})

    footer = html.Div([
        html.Div("Open Exceptions", style={
            "fontSize": "12px", "fontWeight": "700", "marginBottom": "8px",
            "color": TEXT_DARK, "fontFamily": FONT_FAMILY,
        }),
        html.Div(id="alerts-table"),
    ], style={**CARD_STYLE, "marginBottom": "16px"})

    return html.Div([
        header,
        html.Div([kpi_row, charts_mid, charts_bot, footer],
                 style={"padding": "0 20px"}),
    ], style={"backgroundColor": BG, "minHeight": "100vh", "fontFamily": FONT_FAMILY})
