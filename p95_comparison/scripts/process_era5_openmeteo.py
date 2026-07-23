"""ERA5 (Open-Meteo point samples) -> days above local p95, CONUS weighted.
Per-point threshold: p95 of daily TMax 1961-1990. Local-time days.
"""
import glob
import gzip
import os

import numpy as np
import pandas as pd

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/p95_comparison"
files = sorted(glob.glob(f"{BASE}/data/era5/openmeteo/p_*.csv.gz"))
print(f"{len(files)} points")

per_point = []
for fp in files:
    name = os.path.basename(fp)[2:-7]
    la, lo = map(float, name.rsplit("_", 1))
    if int(round(la - 24.5)) % 2 != 0 or int(round(lo + 125.5)) % 2 != 0:
        continue   # keep the uniform 2-deg lattice only
    df = pd.read_csv(fp)
    df["date"] = pd.to_datetime(df.date)
    df = df.dropna(subset=["tmax"])
    df["year"] = df.date.dt.year
    base = df[(df.year >= 1961) & (df.year <= 1990)].tmax
    if len(base) < 10000:
        continue
    th = np.percentile(base, 95)
    g = df.groupby("year").agg(n=("tmax", lambda v: (v > th).sum()),
                               nd=("tmax", "size"))
    g = g[g.nd >= 355]
    g["n"] = g.n * 365.25 / g.nd
    for y, r in g.iterrows():
        per_point.append({"lat": la, "lon": lo, "year": int(y), "n": r.n})

pp = pd.DataFrame(per_point)
pp["w"] = np.cos(np.deg2rad(pp.lat))
res = pp.groupby("year").apply(
    lambda g: (g.n * g.w).sum() / g.w.sum(), include_groups=False).rename("era5")
npts = pp.groupby("year").size()
out = pd.DataFrame({"era5": res, "n_points": npts})
out.round(3).to_csv(f"{BASE}/results/conus_p95_era5.csv")
print(out.head(3).to_string())
print(out.tail(3).to_string())
print(f"\n1961-90 mean (expect ~18.3): {res.loc[1961:1990].mean():.2f}")
print(f"1930s n/a; 2000-23: {res.loc[2000:2023].mean():.2f}  2014-23: {res.loc[2014:2023].mean():.2f}")
