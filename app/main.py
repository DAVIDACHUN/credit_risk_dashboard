"""
Entry point — run with:
    python3 app/main.py
Then open http://127.0.0.1:8050
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import dash
import dash_bootstrap_components as dbc

from data.loaders       import load_all, available_dates, available_books
from app.layout         import build_layout
from app.callbacks      import register_callbacks

# ── load data ───────────────────────────────────────────────────────────────
data  = load_all()
dates = available_dates(data["pnl"])
books = available_books(data["pnl"])

# ── init app ────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Credit Risk Dashboard",
    suppress_callback_exceptions=True,
)
app.layout = build_layout(dates, books)
register_callbacks(app, data)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
