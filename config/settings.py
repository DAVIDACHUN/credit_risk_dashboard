from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parent.parent
DATA_DIR   = BASE_DIR / "data" / "sample_data"
CONFIG_DIR = BASE_DIR / "config"

BOOK_IDS   = ["HY-CREDIT-01"]
DATE_FMT   = "%Y-%m-%d"

# P&L decomposition components (order matters for stacked charts)
PNL_COMPONENTS = ["carry", "spread", "roll", "basis", "event", "residual"]

SECTOR_COLORS = {
    "Software":       "#4C78A8",
    "Healthcare":     "#54A24B",
    "Retail":         "#E45756",
    "Industrials":    "#72B7B2",
    "Energy":         "#F58518",
    "Private Credit": "#B279A2",
}

RATING_ORDER = ["AAA","AA+","AA","AA-","A+","A","A-",
                 "BBB+","BBB","BBB-","BB+","BB","BB-",
                 "B+","B","B-","CCC+","CCC","CCC-","D"]
