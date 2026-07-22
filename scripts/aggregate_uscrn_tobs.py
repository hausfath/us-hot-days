"""Build the TOBs artifact data: network-mean days>=95F per year per obs hour,
over a fixed set of USCRN stations complete in every year 2005-2025."""
import json

import numpy as np
import pandas as pd

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days"

d = pd.read_csv(f"{BASE}/results/uscrn_tobs_counts.csv")
d = d[(d.year >= 2005) & (d.year <= 2025)]
d["complete"] = d.n_warm_hours >= 0.95 * 5136

years = list(range(2005, 2026))
for min_years in [21, 20, 19, 18]:
    ny = d[d.complete].groupby("station").year.nunique()
    keep = ny[ny >= min_years].index
    print(f"stations complete in >={min_years}/21 years: {len(keep)}")

# fixed set: complete in >=20 of 21 years
ny = d[d.complete].groupby("station").year.nunique()
keep = ny[ny >= 20].index
dd = d[d.station.isin(keep) & d.complete]
print(f"\nUsing {len(keep)} stations; station-years: {len(dd)}")

hcols = [f"h{H}" for H in range(24)]
mat = dd.groupby("year")[hcols].mean().reindex(years)
nstn = dd.groupby("year").size().reindex(years)

out = {
    "years": years,
    "n_stations": [int(x) if pd.notna(x) else None for x in nstn],
    "matrix": [[round(float(mat.loc[y, h]), 3) if pd.notna(mat.loc[y, h]) else None
                for h in hcols] for y in years],
}
with open(f"{BASE}/results/uscrn_tobs_matrix.json", "w") as f:
    json.dump(out, f)

true = mat["h0"]
print("\nNetwork mean days >=95F (fixed set):")
print(pd.DataFrame({"true(h0)": true, "5PM(h17)": mat.h17, "7AM(h7)": mat.h7,
                    "n": nstn}).round(2).to_string())
print(f"\nMean inflation 5PM vs true: {(mat.h17/true).mean():.3f}x")
print(f"Mean inflation by hour (vs h0): " +
      ", ".join(f"h{H}:{(mat[f'h{H}']/true).mean():.3f}" for H in [0, 7, 12, 15, 16, 17, 18, 19]))

from scipy import stats
yr = np.array(years, dtype=float)
tr_true = stats.linregress(yr, true).slope * 10
f = (yr - yr[0]) / (yr[-1] - yr[0])
trans = (1 - f) * mat.h17.values + f * mat.h7.values
tr_trans = stats.linregress(yr, trans).slope * 10
print(f"\nTrend 2005-2025, true: {tr_true:+.2f} days/decade")
print(f"Trend, network converting 5PM->7AM: {tr_trans:+.2f} days/decade")
print(f"Fabricated trend: {tr_trans - tr_true:+.2f} days/decade")
