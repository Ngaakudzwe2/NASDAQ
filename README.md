# NASDAQ — NAS100 5-Minute Opening Momentum: analysis, fixed rules and backtester

## What's here

```
NASDAQ/
├── docs/
│   ├── ANALYSIS.md            problems found in the original rules
│   └── STRATEGY_RULES_v2.md   the fixed, fully defined rules
├── config.yaml                every strategy/risk/cost setting
├── run_backtest.py            main entry point
├── src/nasdaq_bt/             engine, data loader, indicators, metrics
├── scripts/
│   ├── make_sample_data.py    synthetic data (for testing the code only)
│   └── fetch_yfinance.py      last ~60 days of NQ=F 5-min data
├── tests/test_engine.py       unit tests for the rules
├── data/                      put your M5 CSV here
└── results/                   trades CSV, summary JSON, equity.png
```

## Setup (VS Code)

1. Open the `NASDAQ` folder in VS Code (**File → Open Folder**).
2. In the terminal:
   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Choose the `.venv` interpreter when VS Code asks.

## Run

```bash
python -m pytest                                        # check the rules logic (10 tests)
python scripts/make_sample_data.py                      # synthetic data (pipeline check only)
python run_backtest.py --csv data/sample_M5.csv --tz UTC --compare
```

With your real data (see `data/README.md`):

```bash
python run_backtest.py --compare              # original vs v2, overnight vs intraday
python run_backtest.py --split 2023-01-01     # in-sample vs out-of-sample
```

You can also use the **Run and Debug** panel. The launch configs are ready.

## Reading the output

| Metric | Look for |
|---|---|
| profit_factor (after costs) | ≥ 1.2, **out-of-sample** |
| expectancy_R | > 0.05 R per trade |
| LONG vs SHORT | Both positive. If only longs work, it's probably just the bull market. |
| buy_and_hold_% | The strategy should beat it on a risk-adjusted basis |
| max_losing_streak | Your risk % must survive it |
| total_swap | How much holding overnight costs |

## Next steps

1. Get 2019–2026 M5 data and run `--compare`.
2. Tune `stop_atr_mult` / `trail_atr_mult` **only on in-sample** data, then confirm with `--split`.
3. Paper trade for 2–3 months before using real money.

*Research tool only, not financial advice.*
