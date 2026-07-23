"""JRA-3Q daily TMax -> days above local (per-cell) p95, CONUS area-weighted.
Threshold: per-cell 95th percentile of daily max, 1961-1990 (values in K;
thresholds and counts are unit-agnostic).
"""
import glob
import json

import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.path import Path as MplPath

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/p95_comparison"
files = sorted(glob.glob(f"{BASE}/data/jra3q/tmax_daily_*.nc"))
print(f"{len(files)} year files")

first = xr.open_dataset(files[0])
lats = first.lat.values
lons = first.lon.values
lons180 = np.where(lons > 180, lons - 360, lons)

gj = json.load(open(f"{BASE}/../hot_days_95F/data/us-states.json"))
lon2, lat2 = np.meshgrid(lons180, lats)
pts = np.column_stack([lon2.ravel(), lat2.ravel()])
inside = np.zeros(len(pts), bool)
for f in gj["features"]:
    if f["properties"]["name"] in {"Alaska", "Hawaii", "Puerto Rico"}:
        continue
    geom = f["geometry"]
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for poly in polys:
        inside |= MplPath(np.array(poly[0])).contains_points(pts)
mask = inside.reshape(lat2.shape)
print(f"CONUS cells: {mask.sum()} of {mask.size}")

base = []
for fp in files:
    y = int(fp.split("_")[-1][:4])
    if 1961 <= y <= 1990:
        base.append(xr.open_dataset(fp).tmax.values)
base = np.concatenate(base, axis=0)
print(f"base days: {base.shape[0]}")
thresh = np.nanpercentile(base, 95, axis=0)
del base
np.save(f"{BASE}/results/jra3q_p95_threshold.npy", thresh)

w = np.cos(np.deg2rad(lats))[:, None] * np.ones_like(thresh) * mask
rows = []
for fp in files:
    y = int(fp.split("_")[-1][:4])
    vals = xr.open_dataset(fp).tmax.values
    if vals.shape[0] < 355:
        continue
    cnt = (vals > thresh[None]).sum(axis=0) * 365.25 / vals.shape[0]
    rows.append({"year": y, "jra3q": float((cnt * w).sum() / w.sum())})
res = pd.DataFrame(rows).set_index("year")
res.round(3).to_csv(f"{BASE}/results/conus_p95_jra3q.csv")
print(res.head(3).to_string(), "\n...\n", res.tail(3).to_string())
print(f"\n1961-90 mean (expect ~18.3): {res.jra3q.loc[1961:1990].mean():.2f}")
print(f"2000-23: {res.jra3q.loc[2000:2023].mean():.2f}")
