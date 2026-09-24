"""Download recent 5-minute Nasdaq-100 futures data (NQ=F) from Yahoo Finance.

Yahoo only gives about the LAST 60 DAYS of 5-minute data. Use it for a quick sanity
check, not for a real backtest. For 2019+ use your broker export or Dukascopy (see data/README.md).

Usage: pip install yfinance && python scripts/fetch_yfinance.py
"""
from pathlib import Path

import yfinance as yf

df = yf.download("NQ=F", interval="5m", period="60d", auto_adjust=False, progress=False)
if df.empty:
    raise SystemExit("No data returned.")
if hasattr(df.columns, "levels"):
    df.columns = df.columns.get_level_values(0)
df = df.rename(columns=str.lower)[["open", "high", "low", "close"]]
df.index = df.index.tz_convert("UTC")
df.index.name = "datetime"
out = Path("data/NQ_yf_M5.csv")
out.parent.mkdir(exist_ok=True)
df.to_csv(out)
print(f"Saved {len(df):,} bars to {out}. Run: python run_backtest.py --csv {out} --tz UTC")
