# Data

Put a 5-minute NAS100 CSV here as `NAS100_M5.csv` (or set `data.csv_path` in `config.yaml`).

Accepted formats:
- `datetime,open,high,low,close[,volume]`
- A MetaTrader 5 export (`<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> ...`, tab-separated)

**Set `data.csv_timezone` correctly.** It's the most common mistake. If it's wrong, the "09:30 candle" is the wrong candle.
- MT5 brokers usually use server time GMT+2 in winter and GMT+3 in summer. Many follow New York's DST, which is `Etc/GMT-2`/`-3` style. Check: the 09:30 New York candle should show a big volume/range spike.
- TradingView and Dukascopy exports can be set to UTC. Use `UTC`.

## Where to get 2019+ M5 data
1. **Your broker's MT5:** Tools → History Center / Symbols → Bars → export US100/NAS100 M5. This is best, because the data matches what you'd trade.
2. **Dukascopy** (free): the historical data feed for USA500/USATECH index CFD, M5, 2019–today.
3. **Yahoo** (`scripts/fetch_yfinance.py`): only the last 60 days. Use it for a quick check only.

Large CSVs are git-ignored.
