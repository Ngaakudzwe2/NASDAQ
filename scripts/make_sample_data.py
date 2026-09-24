"""Generate SYNTHETIC NAS100-like M5 data so the code can be tested without a broker export.

The results on this data mean nothing. It is only for checking that the pipeline runs.
Usage: python scripts/make_sample_data.py --years 2
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--years", type=float, default=2)
p.add_argument("--out", default="data/sample_M5.csv")
p.add_argument("--seed", type=int, default=7)
a = p.parse_args()

rng = np.random.default_rng(a.seed)
idx = pd.date_range("2022-01-03", periods=int(a.years * 365 * 288), freq="5min", tz="America/New_York")
# CFD-style hours: closed Fri 17:00 -> Sun 18:00, daily break 17:00-18:00
wd, hr = idx.weekday, idx.hour
open_mask = ~((wd == 5) | ((wd == 4) & (hr >= 17)) | ((wd == 6) & (hr < 18)) | (hr == 17))
idx = idx[open_mask]

# higher volatility around the cash open
minutes = idx.hour * 60 + idx.minute
vol = np.where((minutes >= 570) & (minutes < 660), 0.0012, 0.0005)
ret = rng.normal(0.000002, vol)
close = 12000 * np.exp(np.cumsum(ret))
open_ = np.r_[close[0], close[:-1]]
spread = np.abs(rng.normal(0, vol * close * 0.8))
high = np.maximum(open_, close) + spread
low = np.minimum(open_, close) - spread

df = pd.DataFrame({"datetime": idx.tz_convert("UTC").strftime("%Y-%m-%d %H:%M:%S"),
                   "open": open_.round(2), "high": high.round(2),
                   "low": low.round(2), "close": close.round(2)})
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
df.to_csv(a.out, index=False)
print(f"Wrote {len(df):,} synthetic bars to {a.out} (timestamps in UTC)")
