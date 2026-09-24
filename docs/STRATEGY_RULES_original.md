# Nasdaq (NAS100) 5-Minute Opening Momentum Strategy

## Strategy Overview
This quantitative trading system captures momentum driven by the New York market open on the Nasdaq 100 index (NAS100). Rather than predicting market direction, it enters based on the closing direction of the first 5-minute candle relative to a exponential moving average, then trails the trade to extract maximum profit from continuous trends.

---

## Technical Specifications & Setup

* **Asset:** NAS100 / US Tech 100 CFD
* **Chart Timeframe:** 5-Minute ($M5$)
* **Key Indicator:** 12-period Exponential Moving Average ($12\text{ EMA}$)
* **Key Session Time:** 09:30 EST (New York Open)

---

## Strategy Rules

### 1. Entry Logic

1. **Wait for the New York Open (09:30 EST):** Do not enter any trade prior to the first 5-minute bar close.
2. **Evaluate Candle #1 (09:30 - 09:35 EST):**
   * **Long Entry Trigger:** If the first 5-minute candle closes **bullish and above** the $12\text{ EMA}$, open a **BUY / LONG** position immediately at the open of the second candle (09:35 EST).
   * **Short Entry Trigger:** If the first 5-minute candle closes **below** the $12\text{ EMA}$, open a **SELL / SHORT** position immediately at the open of the second candle (09:35 EST).

---

### 2. Trade Management & Exit Rules

* **Take Profit:** **No fixed profit target.**
* **Stop Loss Management:**
  * Set an initial stop loss and dynamically update it into a ** trailing stop** as price moves in the trade's favor.
  * The position stays open across market sessions (including overnight and weekends, if applicable) as long as the trailing stop logic is not triggered.
* **Exit Logic:** The position is closed **only** when price retraces and triggers the dynamic trailing stop.

---

## Historical Performance & Backtest Data

* **Backtest Period:** 2019 – 2026
* **Sample Size:** 1,448 historical Nasdaq trades
* **Win Rate:** $57\%$
* **Historical Return:** $+982\%$
* **Profit Factor:** $1.29$
* **Max Drawdown:** $19.7\%$