"""
Data loaders — reads CSVs from sample_data/.
Phase 3 replaces these with SQL queries via extract.py.
"""

from __future__ import annotations
from typing import List
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "sample_data"


def _read(fname: str, parse_dates=("date",)) -> pd.DataFrame:
    path = DATA_DIR / fname
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run: python3 data/sample_data/generate_sample.py"
        )
    df = pd.read_csv(path, parse_dates=list(parse_dates))
    for col in parse_dates:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df


def load_positions() -> pd.DataFrame:
    return _read("positions.csv", parse_dates=())


def load_pnl() -> pd.DataFrame:
    return _read("pnl_daily.csv")


def load_basis() -> pd.DataFrame:
    return _read("basis_data.csv")


def load_hedge() -> pd.DataFrame:
    return _read("hedge_data.csv")


def load_all() -> dict:
    return {
        "positions": load_positions(),
        "pnl":       load_pnl(),
        "basis":     load_basis(),
        "hedge":     load_hedge(),
    }


def available_dates(pnl_df: pd.DataFrame) -> List[str]:
    return sorted(pnl_df["date"].dt.strftime("%Y-%m-%d").unique().tolist())


def available_books(pnl_df: pd.DataFrame) -> List[str]:
    return sorted(pnl_df["book_id"].unique().tolist())
