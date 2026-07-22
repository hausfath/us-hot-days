"""Build the TOBs+MMTS artifact matrix: network-mean days>=95F per
[year][obs hour][bias level], fixed USCRN station set (complete >=20/21 yrs)."""
import json

import numpy as np
import pandas as pd
from scipy import stats

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days"
YEARS = list(range(2005, 2026))
BIASES = [0.0, 0.25, 0.5, 0.75, 1.0]

d = pd.read_csv(f"{BASE}/results/uscrn_tobs_counts2.csv")
d = d[(d.year >= 2005) & (d.year <= 2025)]
d["complete"] = d.n_warm_hours >= 0.95 * 5136
ny = d[d.complete].groupby("station").year.nunique()
keep = ny[ny >= 20].index
dd = d[d.station.isin(keep) & d.complete]
print(f"{len(keep)} stations, {len(dd)} station-years")

cols = [f"h{H}_b{k}" for H in range(24) for k in range(5)]
mat = dd.groupby("year")[cols].mean().reindex(YEARS)
nstn = dd.groupby("year").size().reindex(YEARS)

out = {
    "years": YEARS,
    "biases": BIASES,
    "n_stations": [int(x) for x in nstn],
    # matrix[y][H][k]
    "matrix": [[[round(float(mat.loc[y, f"h{H}_b{k}"]), 3) for k in range(5)]
                for H in range(24)] for y in YEARS],
    "episode_station_2012": {},
}
# Manhattan KS 2012 chips for the mechanism panel
r = d[(d.station == "KS_Manhattan_6_SSW") & (d.year == 2012)].iloc[0]
out["episode_station_2012"] = {"true": int(r.h0_b0), "pm5": int(r.h17_b0),
                               "am7": int(r.h7_b0), "pm5_mmts": int(r.h17_b2)}
with open(f"{BASE}/results/uscrn_tobs_matrix2.json", "w") as f:
    json.dump(out, f)

# headline scenario stats
yr = np.array(YEARS, float)
f = (yr - yr[0]) / (yr[-1] - yr[0])
true = np.array([mat.loc[y, "h0_b0"] for y in YEARS])
pm5 = np.array([mat.loc[y, "h17_b0"] for y in YEARS])
am7 = np.array([mat.loc[y, "h7_b0"] for y in YEARS])
pm5_m = np.array([mat.loc[y, "h17_b2"] for y in YEARS])   # 5PM + MMTS -0.5C
am7_m = np.array([mat.loc[y, "h7_b2"] for y in YEARS])    # 7AM + MMTS -0.5C

scen = {
    "true": true,
    "tobs only (5PM->7AM)": (1 - f) * pm5 + f * am7,
    "mmts only (at 5PM)": (1 - f) * pm5 + f * pm5_m,
    "combined (5PM->7AM+MMTS)": (1 - f) * pm5 + f * am7_m,
}
print(f"\nMMTS -0.5C effect on counts (5PM obs): {pm5_m.mean()/pm5.mean():.3f}x")
for name, ser in scen.items():
    tr = stats.linregress(yr, ser).slope * 10
    print(f"{name:28s} trend {tr:+.2f} days/decade")
