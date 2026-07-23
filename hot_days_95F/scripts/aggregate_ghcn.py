"""Aggregate GHCN station hot-day counts to a CONUS area-weighted average.

- Station-year valid if >=80% of Apr-Oct days have QC'd TMAX (>=172 of 214).
- Station kept if valid in >=85% of years 1895-2025.
- Grid kept stations to 2x2 degree cells, average stations within cell,
  then cos(lat)-weighted average over cells (cells present >=95% of years).
(A stricter 90%/90% variant, 298 stations, gives nearly identical results:
 r=0.99, 1930s/2000-2023 ratio 1.93 vs 1.75. See METHODS.md.)
"""
import numpy as np
import pandas as pd

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/hot_days_95F"
Y0, Y1 = 1895, 2025
YEARS = np.arange(Y0, Y1 + 1)

counts = pd.read_csv(f"{BASE}/results/ghcn_station_annual_counts.csv")
meta = pd.read_csv(f"{BASE}/data/ghcn/candidate_stations.csv")[["id", "lat", "lon"]]

counts = counts[(counts.year >= Y0) & (counts.year <= Y1)]
counts["valid"] = counts.warm_days >= 172

# Station screening: valid in >=85% of the 131 years
nvalid = counts[counts.valid].groupby("id").year.nunique()
keep = nvalid[nvalid >= 0.85 * len(YEARS)].index
print(f"Stations kept: {len(keep)} of {counts.id.nunique()}")

df = counts[counts.id.isin(keep) & counts.valid].merge(meta, on="id")
df["latbin"] = (np.floor((df.lat - 24) / 2) * 2 + 25).astype(int)   # cell centers
df["lonbin"] = (np.floor((df.lon + 126) / 2) * 2 - 125).astype(int)

# Cell-year means
cell = df.groupby(["latbin", "lonbin", "year"])[["n95", "n100", "n105"]].mean()
cell["nstn"] = df.groupby(["latbin", "lonbin", "year"]).size()
cell = cell.reset_index()

# Fixed cell mask: present in >=95% of years
cover = cell.groupby(["latbin", "lonbin"]).year.nunique()
good_cells = cover[cover >= 0.95 * len(YEARS)].index
cell = cell.set_index(["latbin", "lonbin"]).loc[good_cells].reset_index()
pd.DataFrame(list(good_cells), columns=["latbin", "lonbin"]).to_csv(
    f"{BASE}/results/ghcn_cells_used.csv", index=False)
print(f"Grid cells used: {len(good_cells)}, "
      f"stations in them: {df.set_index(['latbin','lonbin']).loc[good_cells].id.nunique()}")

cell["w"] = np.cos(np.deg2rad(cell.latbin))
out = []
for y, g in cell.groupby("year"):
    w = g.w / g.w.sum()
    out.append({
        "year": y,
        "n95": (g.n95 * w).sum(),
        "n100": (g.n100 * w).sum(),
        "n105": (g.n105 * w).sum(),
        "n_cells": len(g),
        "n_stations": g.nstn.sum(),
    })
res = pd.DataFrame(out)
res.to_csv(f"{BASE}/results/ghcn_conus_annual.csv", index=False)

# Naive unweighted station mean for comparison
naive = df.groupby("year")[["n95", "n100", "n105"]].mean().reset_index()
naive.to_csv(f"{BASE}/results/ghcn_conus_annual_naive.csv", index=False)

print(res.tail(3).round(2).to_string(index=False))
print("Decadal means, days >=95F (gridded):")
res["dec"] = (res.year // 10) * 10
print(res.groupby("dec").n95.mean().round(2).to_string())
