"""Load M5 OHLC data from CSV and convert it to New York time."""
from __future__ import annotations

import pandas as pd

NY_TZ = "America/New_York"

_ALIASES = {
    "time": "datetime", "date": "datetime", "timestamp": "datetime", "date_time": "datetime",
    "o": "open", "h": "high", "l": "low", "c": "close",
}


def load_csv(path: str, csv_timezone: str = "UTC", start=None, end=None) -> pd.DataFrame:
    """Read a CSV with columns datetime, open, high, low, close (volume optional).

    Handles MT5 exports where date and time are separate columns (<DATE>, <TIME>).
    Returns a DataFrame indexed by tz-aware New York timestamps (bar OPEN time).
    """
    sep = "\t" if open(path, encoding="utf-8").readline().count("\t") > 1 else ","
    df = pd.read_csv(path, sep=sep)
    df.columns = [c.strip().strip("<>").lower() for c in df.columns]

    if "date" in df.columns and "time" in df.columns:  # MT5 style
        df["datetime"] = df["date"].astype(str) + " " + df["time"].astype(str)
        df = df.drop(columns=["date", "time"])
    df = df.rename(columns={k: v for k, v in _ALIASES.items() if k in df.columns})

    missing = {"datetime", "open", "high", "low", "close"} - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {sorted(missing)} (found {list(df.columns)})")

    ts = pd.to_datetime(df["datetime"], utc=False)
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize(csv_timezone, ambiguous="NaT", nonexistent="NaT")
    df.index = ts.dt.tz_convert(NY_TZ)
    df = df[df.index.notna()]
    df = df[["open", "high", "low", "close"]].astype(float)
    df = df[~df.index.duplicated(keep="first")].sort_index()

    if start:
        df = df[df.index >= pd.Timestamp(start, tz=NY_TZ)]
    if end:
        df = df[df.index <= pd.Timestamp(end, tz=NY_TZ)]
    if df.empty:
        raise ValueError("No data left after loading/filtering.")
    return df
