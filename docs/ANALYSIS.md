# Analysis of the original rules

## Gaps in the rules

| # | Problem | Why it matters | Fix in v2 |
|---|---|---|---|
| 1 | Long needs a bullish candle above the EMA; short only needs a close below the EMA | A **bullish** candle that closes below the EMA gives a short. That's contradictory. | Both sides need the candle direction and the EMA side to agree |
| 2 | Initial stop and trailing method never defined | There's no take-profit, so the stop decides every result. The backtest can't be reproduced. | ATR stop and ATR chandelier trail, both settings you can change |
| 3 | No rule for a trade still open at the next 09:30 | You could stack positions without meaning to | One position at a time |
| 4 | No position sizing | +982% is meaningless without the size/leverage used | Fixed % risk per trade |
| 5 | Costs not stated | A profit factor of 1.29 is thin. Spread, slippage at the open, swaps and weekend gaps can wipe it out. | All modelled |
| 6 | "09:30 EST" | New York uses EDT in summer. Berlin time shifts to 14:30 during the clock-change gaps. | Uses the New York time zone |

## The numbers don't add up

- A 57% win rate with a profit factor of 1.29 means **average win ≈ 0.97 × average loss**. A "let winners run" trend system usually shows the opposite: a lower win rate and bigger winners.
- +982% over about 7.7 years is roughly **36% a year** with a max drawdown of only 19.7%. That's very high for the risk; it points to leverage or compounding, or an optimistic test.
- 2019–2026 was mostly a strong bull market, so a long bias flatters the results. Long and short results need to be shown separately.
- With a 43% loss rate over about 1,450 trades, a streak of **about 8 losses in a row** is expected.

## Verdict

It's a reasonable hypothesis, but it isn't proven. Test v2 on your own data with costs before trading it.
