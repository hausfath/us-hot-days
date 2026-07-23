"""ERA5 daily TMax -> days above local (per-cell) p95, CONUS area-weighted.
Threshold: per-cell 95th percentile of daily max t2m, 1961-1990.
"""
import glob
import json

import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.path import Path as MplPath

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/p95_comparison"

files = sorted(glob.glob(f"{BASE}/data/era5/raw/tmax_*.nc"))
print(f"{len(files)} year files")

def open_year(fp):
    ds = xr.open_dataset(fp)
    var = "t2m" if "t2m" in ds else list(ds.data_vars)[0]
    da = ds[var]
    tdim = "valid_time" if "valid_time" in da.dims else "time"
    da = da.rename({tdim: "time"})
    return da

first = open_year(files[0])
lats, lons = first.latitude.values, first.longitude.values

# CONUS mask at ERA5 resolution
gj = json.load(open(f"{BASE}/../hot_days_95F/data/us-states.json"))
lon2, lat2 = np.meshgrid(lons, lats)
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

# threshold from 1961-1990
base = []
for fp in files:
    y = int(fp.split("_")[-1][:4])
    if 1961 <= y <= 1990:
        base.append(open_year(fp).values)
base = np.concatenate(base, axis=0)
print(f"base days: {base.shape[0]}")
thresh = np.nanpercentile(base, 95, axis=0)
del base
np.save(f"{BASE}/results/era5_p95_threshold.npy", thresh)

w = np.cos(np.deg2rad(lats))[:, None] * np.ones_like(thresh) * mask
rows = []
for fp in files:
    y = int(fp.split("_")[-1][:4])
    da = open_year(fp)
    vals = da.values
    if vals.shape[0] < 355:          # incomplete year
        continue
    cnt = (vals > thresh[None]).sum(axis=0)
    rows.append({"year": y,
                 "era5": float((cnt * w).sum() / w.sum()),
                 "ndays": int(vals.shape[0])})
res = pd.DataFrame(rows).set_index("year")
res.round(3).to_csv(f"{BASE}/results/conus_p95_era5.csv")
print(res.head(3).to_string(), "\n...\n", res.tail(3).to_string())
print(f"\n1961-90 mean (should be ~18.3): {res.era5.loc[1961:1990].mean():.2f}")
