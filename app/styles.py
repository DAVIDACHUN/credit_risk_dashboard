"""
Centralised style constants — Power-BI-style light theme.
"""

BG          = "#F4F6FA"
CARD_BG     = "#FFFFFF"
PRIMARY     = "#0078D4"
POS_GREEN   = "#107C41"
NEG_RED     = "#C4314B"
WARN_AMBER  = "#F7971C"
TEXT_DARK   = "#1F2937"
TEXT_MID    = "#6B7280"
BORDER      = "#E5E7EB"

FONT_FAMILY = "Inter, Segoe UI, sans-serif"

CARD_STYLE = {
    "background": CARD_BG,
    "borderRadius": "8px",
    "boxShadow": "0 1px 4px rgba(0,0,0,0.08)",
    "padding": "16px 20px",
    "border": f"1px solid {BORDER}",
}

KPI_VALUE_STYLE = {
    "fontSize": "26px",
    "fontWeight": "700",
    "lineHeight": "1.1",
    "fontFamily": FONT_FAMILY,
}

KPI_LABEL_STYLE = {
    "fontSize": "11px",
    "fontWeight": "600",
    "color": TEXT_MID,
    "textTransform": "uppercase",
    "letterSpacing": "0.06em",
    "fontFamily": FONT_FAMILY,
    "marginBottom": "4px",
}

CHART_LAYOUT = dict(
    paper_bgcolor=CARD_BG,
    plot_bgcolor=CARD_BG,
    font=dict(family=FONT_FAMILY, color=TEXT_DARK, size=12),
    margin=dict(l=40, r=20, t=36, b=36),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(showgrid=False, linecolor=BORDER),
    yaxis=dict(gridcolor=BORDER, zeroline=True, zerolinecolor=BORDER),
)

SECTOR_COLORS = {
    "Software":       "#4C78A8",
    "Healthcare":     "#54A24B",
    "Retail":         "#E45756",
    "Industrials":    "#72B7B2",
    "Energy":         "#F58518",
    "Private Credit": "#B279A2",
}

STATUS_COLORS = {
    "OK":     POS_GREEN,
    "WARN":   WARN_AMBER,
    "BREACH": NEG_RED,
}
