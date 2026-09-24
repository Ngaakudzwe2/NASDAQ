# NAS100 5-Minute Opening Momentum Strategy — Rules v2 (fixed)

This version fixes every gap found in the original rules (see `ANALYSIS.md`).
Every value marked **[param]** is a setting in `config.yaml`, so each one can be tested.

---

## 1. Setup

| Item | Value |
|---|---|
| Instrument | NAS100 / US Tech 100 CFD (or NQ futures for research) |
| Chart | 5-minute (M5) |
| Indicators | EMA(12) on close; ATR(14) on M5 |
| Session clock | **America/New_York**, so summer/winter time is handled automatically |
| Open | 09:30 New York = 15:30 Berlin (14:30 Berlin during the US/EU clock-change gaps) |
| EMA data | Calculated on **all** broker bars, including pre-market. Always use the same data feed. |

## 2. Entry (symmetric: FIX #1)

Signal candle = the M5 bar that opens at 09:30 New York.

| Condition at close of signal candle | Action |
|---|---|
| close > open **AND** close > EMA12 | **BUY** at the open of the next bar (09:35) |
| close < open **AND** close < EMA12 | **SELL** at the open of the next bar (09:35) |
| Anything else (candle and EMA disagree, or a doji) | **No trade today** |

Optional filters, off by default **[param]**:
- `min_body_atr`: skip if the candle body is smaller than X × ATR (removes weak candles).
- `skip_weekdays`: e.g. skip Fridays.

## 3. Initial stop loss (defined: FIX #2)

**[param] `stop_mode`**
- `atr` (default): stop = entry ∓ `stop_atr_mult` × ATR(14). Default is 1.5.
- `candle`: stop just beyond the signal candle's low (long) or high (short), plus a 1-point buffer.

## 4. Trailing stop (defined: FIX #2)

A chandelier trail, updated **only after each M5 bar closes**. That way there's no look-ahead.

- Long: trail = highest high since entry − `trail_atr_mult` × ATR(14). Default is 2.5.
- Short: trail = lowest low since entry + `trail_atr_mult` × ATR(14).
- The stop **only moves in the trade's favour**. It never loosens.
- Optional **[param] `breakeven_at_r`**: once a bar **closes** at ≥ X R open profit, move the stop to entry. An intrabar touch doesn't count.

## 5. Exit

- Close the trade when price touches the active stop.
- **Gap rule:** if a bar opens beyond the stop, the fill is at the **open**, not the stop price. That's what really happens on Monday opens.
- **[param] `hold_overnight`**:
  - `true` = the original behaviour: hold across sessions and weekends.
  - `false` = close at 16:00 New York. Used to compare, because CFD overnight fees are removed.

## 6. One position at a time (FIX #3)

If a trade is still open at 09:30, **ignore today's signal**. Positions never stack.

## 7. Position sizing (FIX #4)

- Risk **[param] `risk_pct`** of account equity per trade. Default 0.5%.
- Size = (equity × risk_pct) / |entry − initial stop|.
- Position value is capped at **[param] `max_leverage`** × equity (default 20). When the stop is tight, the cap can make the real risk smaller than `risk_pct`.
- **Maximum 1 open position.** No pyramiding.

## 8. Costs, all included in the backtest (FIX #5)

| Cost | Default **[param]** |
|---|---|
| Spread | 1.5 points per round trip |
| Slippage at entry (09:35) | 1.0 point |
| Slippage on stop fills | 1.0 point |
| Overnight financing | charged per night held, as `swap_pct_per_year` of the position value |

## 9. How to validate before real money

1. Backtest on at least 5 years of M5 data from **your broker** (or Dukascopy).
2. Report **long and short results separately**, plus buy-and-hold over the same period.
3. **Walk-forward:** tune on 2019–2022, then test on 2023–2026 without changing anything.
4. Accept it only if the out-of-sample profit factor is ≥ 1.2 after costs, and the max drawdown is tolerable.
5. Paper trade for 2–3 months. Live results should stay within the backtest's range.
