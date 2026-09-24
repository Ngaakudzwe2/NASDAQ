"""Bar-by-bar backtest engine for the NAS100 5-minute opening momentum strategy (rules v2).

Conventions
-----------
* Index = bar OPEN time in America/New_York.
* Signal is read at the CLOSE of the 09:30 bar; entry at the OPEN of the 09:35 bar.
* Stops are checked against each bar's high/low. If a bar opens through the stop, the
  fill is at the open (gap). The trailing stop is updated only after a bar closes, so there is
  no look-ahead.
* 1 CFD unit = 1 currency unit per index point.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import RiskConfig, StrategyConfig
from .indicators import atr as calc_atr
from .indicators import ema as calc_ema


@dataclass
class _Position:
    direction: int          # +1 long, -1 short
    entry_time: pd.Timestamp
    entry_price: float
    stop: float
    initial_stop: float
    units: float
    risk_amount: float
    extreme: float          # best price since entry (high for long, low for short)
    entry_day: int
    breakeven_done: bool = False


def _hhmm_to_min(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _signal(o, c, e, rule: str) -> int:
    """+1 long, -1 short, 0 no trade."""
    if rule == "original":
        if c > o and c > e:
            return 1
        if c < e:
            return -1          # original rule: any close below EMA, even a bullish candle
        return 0
    # symmetric (v2)
    if c > o and c > e:
        return 1
    if c < o and c < e:
        return -1
    return 0


def _rollover_nights(entry: pd.Timestamp, exit_: pd.Timestamp) -> int:
    """Number of 17:00 New York rollovers crossed (Fri->Mon counts 3, as at most brokers)."""
    a = (entry.tz_localize(None) - pd.Timedelta(hours=17)).normalize()
    b = (exit_.tz_localize(None) - pd.Timedelta(hours=17)).normalize()
    return max(0, (b - a).days)


def run_backtest(df: pd.DataFrame, s: StrategyConfig, r: RiskConfig):
    """Run the backtest. Returns (trades DataFrame, equity Series indexed by exit time)."""
    df = df.copy()
    df["ema"] = calc_ema(df["close"], s.ema_period)
    df["atr"] = calc_atr(df, s.atr_period)

    idx = df.index
    o, h, l, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    ema_v, atr_v = df["ema"].to_numpy(), df["atr"].to_numpy()
    minute = (idx.hour * 60 + idx.minute).to_numpy()
    day = (idx.year * 10_000 + idx.month * 100 + idx.day).to_numpy()
    weekday = idx.weekday.to_numpy()

    open_min = _hhmm_to_min(s.open_time)
    close_min = _hhmm_to_min(s.session_close)
    half_spread = r.spread_points / 2
    warmup = max(s.ema_period, s.atr_period) * 3

    equity = float(r.initial_equity)
    pos: _Position | None = None
    pending: dict | None = None
    trades: list[dict] = []
    skipped_open = 0

    def close_position(i: int, raw_price: float, reason: str, slip: float):
        nonlocal equity, pos
        d = pos.direction
        fill = raw_price - d * (half_spread + slip)
        gross = d * (fill - pos.entry_price) * pos.units
        nights = _rollover_nights(pos.entry_time, idx[i])
        swap = pos.units * pos.entry_price * (r.swap_pct_per_year / 100) / 365 * nights
        pnl = gross - swap
        trades.append({
            "entry_time": pos.entry_time, "exit_time": idx[i],
            "direction": "long" if d == 1 else "short",
            "entry": round(pos.entry_price, 2), "exit": round(fill, 2),
            "initial_stop": round(pos.initial_stop, 2), "units": pos.units,
            "points": d * (fill - pos.entry_price), "swap": swap, "nights": nights,
            "pnl": pnl, "r_multiple": pnl / pos.risk_amount if pos.risk_amount else np.nan,
            "exit_reason": reason, "equity_before": equity,
        })
        equity += pnl
        pos = None

    for i in range(len(df)):
        # ---- 1. pending entry at this bar's open ------------------------------
        if pending is not None:
            d = pending["dir"]
            entry_price = o[i] + d * (half_spread + r.entry_slippage_points)
            if s.stop_mode == "candle":
                stop = pending["sig_low"] - s.candle_stop_buffer if d == 1 else pending["sig_high"] + s.candle_stop_buffer
            else:
                stop = entry_price - d * s.stop_atr_mult * pending["atr"]
            dist = abs(entry_price - stop)
            if dist > 0 and d * (entry_price - stop) > 0:
                risk_amount = equity * r.risk_pct / 100
                units = risk_amount / dist
                units = min(units, equity * r.max_leverage / entry_price)
                pos = _Position(d, idx[i], entry_price, stop, stop, units,
                                units * dist, o[i], day[i])
            pending = None

        # ---- 2. manage open position -----------------------------------------
        if pos is not None:
            d = pos.direction
            if d * (o[i] - pos.stop) <= 0 and idx[i] != pos.entry_time:
                close_position(i, o[i], "gap_stop", r.stop_slippage_points)
            elif (d == 1 and l[i] <= pos.stop) or (d == -1 and h[i] >= pos.stop):
                close_position(i, pos.stop, "stop", r.stop_slippage_points)
            elif not s.hold_overnight and (day[i] != pos.entry_day):
                close_position(i, o[i], "session_end", 0.0)
            elif not s.hold_overnight and minute[i] + 5 >= close_min:
                close_position(i, c[i], "session_end", 0.0)
            else:
                # bar closed without exit -> update trail for the NEXT bar
                pos.extreme = max(pos.extreme, h[i]) if d == 1 else min(pos.extreme, l[i])
                trail = pos.extreme - d * s.trail_atr_mult * atr_v[i]
                if s.breakeven_at_r > 0 and not pos.breakeven_done:
                    init_dist = abs(pos.entry_price - pos.initial_stop)
                    if d * (c[i] - pos.entry_price) >= s.breakeven_at_r * init_dist:
                        trail = max(trail, pos.entry_price) if d == 1 else min(trail, pos.entry_price)
                        pos.breakeven_done = True
                pos.stop = max(pos.stop, trail) if d == 1 else min(pos.stop, trail)

        # ---- 3. signal on the 09:30 bar close ---------------------------------
        if minute[i] == open_min and i >= warmup and i + 1 < len(df):
            if pos is not None or pending is not None:
                skipped_open += 1
                continue
            if weekday[i] in s.skip_weekdays:
                continue
            # the next bar must be 09:35 on the same day (no data gap)
            if day[i + 1] != day[i] or minute[i + 1] != open_min + 5:
                continue
            if s.min_body_atr > 0 and abs(c[i] - o[i]) < s.min_body_atr * atr_v[i]:
                continue
            d = _signal(o[i], c[i], ema_v[i], s.entry_rule)
            if d != 0:
                pending = {"dir": d, "atr": atr_v[i], "sig_low": l[i], "sig_high": h[i]}

    # close anything still open at the end of the data
    if pos is not None:
        close_position(len(df) - 1, c[-1], "end_of_data", 0.0)

    trades_df = pd.DataFrame(trades)
    if trades_df.empty:
        eq = pd.Series([r.initial_equity], index=[idx[0]], name="equity")
    else:
        eq = pd.Series(trades_df["equity_before"].to_numpy() + trades_df["pnl"].to_numpy(),
                       index=trades_df["exit_time"], name="equity")
        eq = pd.concat([pd.Series([r.initial_equity], index=[idx[0]]), eq]).rename("equity")
    trades_df.attrs["skipped_open_signals"] = skipped_open
    return trades_df, eq
