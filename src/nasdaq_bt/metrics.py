from __future__ import annotations

import numpy as np
import pandas as pd


def _max_streak(wins: np.ndarray, value: bool) -> int:
    best = cur = 0
    for w in wins:
        cur = cur + 1 if w == value else 0
        best = max(best, cur)
    return best


def _block(t: pd.DataFrame) -> dict:
    if t.empty:
        return {"trades": 0}
    wins = t["pnl"] > 0
    gross_win = t.loc[wins, "pnl"].sum()
    gross_loss = -t.loc[~wins, "pnl"].sum()
    avg_win = t.loc[wins, "pnl"].mean() if wins.any() else 0.0
    avg_loss = -t.loc[~wins, "pnl"].mean() if (~wins).any() else 0.0
    return {
        "trades": int(len(t)),
        "win_rate_%": round(100 * wins.mean(), 1),
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else float("inf"),
        "avg_win/avg_loss": round(avg_win / avg_loss, 2) if avg_loss > 0 else float("inf"),
        "expectancy_R": round(t["r_multiple"].mean(), 3),
        "net_pnl": round(t["pnl"].sum(), 2),
        "total_swap": round(t["swap"].sum(), 2),
        "max_losing_streak": _max_streak(wins.to_numpy(), False),
        "avg_nights_held": round(t["nights"].mean(), 2),
    }


def summarize(trades: pd.DataFrame, equity: pd.Series, prices: pd.DataFrame) -> dict:
    out: dict = {}
    start_eq, end_eq = equity.iloc[0], equity.iloc[-1]
    years = max((prices.index[-1] - prices.index[0]).days / 365.25, 1e-9)
    dd = equity / equity.cummax() - 1

    out["period"] = f"{prices.index[0]:%Y-%m-%d} -> {prices.index[-1]:%Y-%m-%d} ({years:.1f} y)"
    out["total_return_%"] = round(100 * (end_eq / start_eq - 1), 1)
    out["CAGR_%"] = round(100 * ((end_eq / start_eq) ** (1 / years) - 1), 1) if end_eq > 0 else -100.0
    out["max_drawdown_%"] = round(100 * dd.min(), 1)
    out["buy_and_hold_%"] = round(100 * (prices["close"].iloc[-1] / prices["close"].iloc[0] - 1), 1)
    out["skipped_signals_position_open"] = trades.attrs.get("skipped_open_signals", 0)
    out["ALL"] = _block(trades)
    if not trades.empty:
        out["LONG"] = _block(trades[trades["direction"] == "long"])
        out["SHORT"] = _block(trades[trades["direction"] == "short"])
        out["exit_reasons"] = trades["exit_reason"].value_counts().to_dict()
    return out


def format_summary(summary: dict, title: str = "") -> str:
    lines = [f"\n=== {title} ===" if title else ""]
    for k, v in summary.items():
        if isinstance(v, dict):
            lines.append(f"  [{k}]")
            for k2, v2 in v.items():
                lines.append(f"      {k2:<22} {v2}")
        else:
            lines.append(f"  {k:<32} {v}")
    return "\n".join(lines)
