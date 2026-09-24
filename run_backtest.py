"""Run the NAS100 opening-momentum backtest.

Examples
--------
python run_backtest.py                       # uses config.yaml
python run_backtest.py --compare             # original vs v2 rules, overnight vs intraday
python run_backtest.py --csv data/sample_M5.csv --tz UTC
python run_backtest.py --split 2023-01-01    # in-sample / out-of-sample check
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from nasdaq_bt.config import load_config  # noqa: E402
from nasdaq_bt.data import load_csv  # noqa: E402
from nasdaq_bt.engine import run_backtest  # noqa: E402
from nasdaq_bt.metrics import format_summary, summarize  # noqa: E402


def run_one(df, cfg, name, out_dir: Path, curves: dict):
    trades, equity = run_backtest(df, cfg.strategy, cfg.risk)
    summary = summarize(trades, equity, df)
    print(format_summary(summary, name))
    safe = name.replace(" ", "_").replace("/", "-")
    trades.to_csv(out_dir / f"trades_{safe}.csv", index=False)
    (out_dir / f"summary_{safe}.json").write_text(json.dumps(summary, indent=2, default=str))
    curves[name] = equity
    return summary


def plot(curves: dict, out_dir: Path):
    fig, ax = plt.subplots(figsize=(11, 5))
    for name, eq in curves.items():
        ax.plot(eq.index, eq.values, label=name, linewidth=1.4)
    ax.set_title("Equity curve (closed trades)")
    ax.set_ylabel("Equity")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "equity.png", dpi=130)
    print(f"\nChart saved: {out_dir / 'equity.png'}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="config.yaml")
    p.add_argument("--csv", help="override data.csv_path")
    p.add_argument("--tz", help="override data.csv_timezone")
    p.add_argument("--compare", action="store_true", help="run original vs v2 variants")
    p.add_argument("--split", help="date: report in-sample before / out-of-sample after")
    a = p.parse_args()

    cfg = load_config(a.config)
    if a.csv:
        cfg.data.csv_path = a.csv
    if a.tz:
        cfg.data.csv_timezone = a.tz

    df = load_csv(cfg.data.csv_path, cfg.data.csv_timezone, cfg.data.start, cfg.data.end)
    print(f"Loaded {len(df):,} bars  {df.index[0]} -> {df.index[-1]}")

    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    curves: dict = {}

    if a.split:
        ins, oos = df[df.index < a.split], df[df.index >= a.split]
        run_one(ins, cfg, "in-sample", out_dir, curves)
        run_one(oos, cfg, "out-of-sample", out_dir, curves)
    elif a.compare:
        variants = {
            "original rules (asym short, hold overnight)": dict(entry_rule="original", hold_overnight=True),
            "v2 symmetric, hold overnight": dict(entry_rule="symmetric", hold_overnight=True),
            "v2 symmetric, intraday only": dict(entry_rule="symmetric", hold_overnight=False),
        }
        for name, over in variants.items():
            c = copy.deepcopy(cfg)
            for k, v in over.items():
                setattr(c.strategy, k, v)
            run_one(df, c, name, out_dir, curves)
    else:
        run_one(df, cfg, "v2", out_dir, curves)

    plot(curves, out_dir)


if __name__ == "__main__":
    main()
