import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nasdaq_bt.config import RiskConfig, StrategyConfig  # noqa: E402
from nasdaq_bt.data import load_csv  # noqa: E402
from nasdaq_bt.engine import _rollover_nights, _signal, run_backtest  # noqa: E402

TZ = "America/New_York"


def make_df(day="2024-07-01", pre=10, first=(100, 106, 99, 105), after=None, days=1):
    """Flat bars at 100 before 09:30, a configurable 09:30 bar, then `after` bars."""
    rows = []
    t = pd.Timestamp(f"{day} 09:30", tz=TZ) - pd.Timedelta(minutes=5 * pre)
    for _ in range(pre):
        rows.append((t, 100, 100.5, 99.5, 100)); t += pd.Timedelta(minutes=5)
    rows.append((t, *first)); t += pd.Timedelta(minutes=5)
    for bar in (after or [(105, 106, 104, 105.5)] * 5):
        rows.append((t, *bar)); t += pd.Timedelta(minutes=5)
    df = pd.DataFrame(rows, columns=["t", "open", "high", "low", "close"]).set_index("t")
    return df.astype(float)


S = dict(ema_period=2, atr_period=2)
R0 = dict(spread_points=0, entry_slippage_points=0, stop_slippage_points=0, swap_pct_per_year=0)


def test_signal_rules():
    assert _signal(100, 105, 101, "symmetric") == 1
    assert _signal(100, 95, 99, "symmetric") == -1
    # bullish candle closing below EMA: original says SHORT, v2 says no trade
    assert _signal(100, 102, 103, "original") == -1
    assert _signal(100, 102, 103, "symmetric") == 0


def test_long_entry_at_next_open_with_costs():
    df = make_df()
    r = RiskConfig(spread_points=2, entry_slippage_points=1, stop_slippage_points=0, swap_pct_per_year=0)
    trades, _ = run_backtest(df, StrategyConfig(**S), r)
    t = trades.iloc[0]
    assert t["direction"] == "long"
    assert t["entry_time"] == pd.Timestamp("2024-07-01 09:35", tz=TZ)
    assert t["entry"] == pytest.approx(105 + 1 + 1)  # open + half spread + slippage


def test_bullish_candle_below_ema_no_trade_in_v2():
    after = [(102, 102.5, 101.5, 102)] * 5
    # pre bars at 110 so EMA is far above the bullish signal candle
    df = make_df(first=(100, 103, 99.5, 102), after=after)
    df.iloc[:10] = [110, 110.5, 109.5, 110]
    t_v2, _ = run_backtest(df, StrategyConfig(**S, entry_rule="symmetric"), RiskConfig(**R0))
    t_orig, _ = run_backtest(df, StrategyConfig(**S, entry_rule="original"), RiskConfig(**R0))
    assert t_v2.empty
    assert t_orig.iloc[0]["direction"] == "short"


def test_stop_fill_with_slippage():
    after = [(105, 105.5, 104.5, 105), (105, 105, 90, 92)]
    df = make_df(after=after)
    # stop = 99 - 1 = 98; wide trail so only the initial stop is active
    s = StrategyConfig(**S, stop_mode="candle", candle_stop_buffer=1, trail_atr_mult=50)
    r = RiskConfig(**{**R0, "stop_slippage_points": 0.5})
    t = run_backtest(df, s, r)[0].iloc[0]
    assert t["exit_reason"] == "stop"
    assert t["exit"] == pytest.approx(98 - 0.5)


def test_gap_through_stop_fills_at_open():
    after = [(105, 105.5, 104.5, 105), (90, 91, 89, 90)]
    df = make_df(after=after)
    s = StrategyConfig(**S, stop_mode="candle", candle_stop_buffer=1)
    t = run_backtest(df, s, RiskConfig(**R0))[0].iloc[0]
    assert t["exit_reason"] == "gap_stop"
    assert t["exit"] == pytest.approx(90)


def test_intraday_mode_exits_at_session_close():
    day1 = make_df(after=[(105, 106, 104.9, 105.5)] * 80)  # runs past 16:00
    s = StrategyConfig(**S, hold_overnight=False, trail_atr_mult=50, stop_atr_mult=50)
    t = run_backtest(day1, s, RiskConfig(**R0))[0].iloc[0]
    assert t["exit_reason"] == "session_end"
    assert t["exit_time"] == pd.Timestamp("2024-07-01 15:55", tz=TZ)


def test_no_stacking_when_position_open():
    a = make_df("2024-07-01", after=[(105, 106, 104.9, 105.5)] * 3)
    b = make_df("2024-07-02", pre=10, after=[(105, 106, 104.9, 105.5)] * 3)
    df = pd.concat([a, b])
    s = StrategyConfig(**S, trail_atr_mult=50, stop_atr_mult=50)
    trades, _ = run_backtest(df, s, RiskConfig(**R0))
    assert len(trades) == 1
    assert trades.attrs["skipped_open_signals"] == 1


def test_trailing_stop_only_tightens():
    up = [(105 + i, 106 + i, 104.8 + i, 105.8 + i) for i in range(10)]
    df = make_df(after=up + [(114, 114, 100, 101)])
    s = StrategyConfig(**S, trail_atr_mult=1.0)
    t = run_backtest(df, s, RiskConfig(**R0))[0].iloc[0]
    assert t["exit_reason"] == "stop"
    assert t["exit"] > t["entry"]  # trail locked in profit


def test_rollover_nights_weekend():
    fri = pd.Timestamp("2024-07-05 10:00", tz=TZ)
    mon = pd.Timestamp("2024-07-08 10:00", tz=TZ)
    assert _rollover_nights(fri, mon) == 3
    assert _rollover_nights(fri, fri + pd.Timedelta(hours=3)) == 0


def test_csv_loader_mt5_format_and_dst(tmp_path):
    f = tmp_path / "mt5.csv"
    f.write_text("<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\n"
                 "2024.07.01\t13:30:00\t1\t2\t0.5\t1.5\n"   # summer: UTC-4
                 "2024.01.02\t14:30:00\t1\t2\t0.5\t1.5\n")  # winter: UTC-5
    df = load_csv(str(f), "UTC")
    assert all(ts.strftime("%H:%M") == "09:30" for ts in df.index)
