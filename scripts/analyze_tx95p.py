"""Days above the local 95th percentile of daily TMax (TX95p-style, absolute
values, per-cell threshold from 1961-1990), from BE daily gridded CONUS
subsets. Aggregates to CONUS and NOAA's nine climate regions.
"""
import glob
import json

import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.path import Path as MplPath

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days"
DEC = list(range(1890, 2030, 10))

# ---------- per-cell 95th percentile threshold, 1961-1990 ----------
chunks = []
for d in [1960, 1970, 1980, 1990]:
    ds = xr.open_dataset(f"{BASE}/data/berkeley/conus_daily_{d}.nc")
    sel = (ds.year.values >= 1961) & (ds.year.values <= 1990)
    chunks.append(ds.tmax.values[sel])
    lats, lons = ds.latitude.values, ds.longitude.values
    land = ds.land_mask.values
    ds.close()
base = np.concatenate(chunks, axis=0)
print(f"base period days: {base.shape[0]}")
thresh = np.nanpercentile(base, 95, axis=0)   # (lat, lon)
del base, chunks
np.save(f"{BASE}/results/tx95p_threshold.npy", thresh)
print(f"threshold range over CONUS box: {np.nanmin(thresh):.1f} to "
      f"{np.nanmax(thresh):.1f} C")

# ---------- per-cell annual exceedance counts, all years ----------
counts, nvalid, years_all = [], [], []
for d in DEC:
    ds = xr.open_dataset(f"{BASE}/data/berkeley/conus_daily_{d}.nc")
    tm = ds.tmax.values
    yr = ds.year.values
    for y in np.unique(yr):
        sel = yr == y
        block = tm[sel]
        valid = np.isfinite(block)
        counts.append((block > thresh[None, :, :]).sum(axis=0, where=valid))
        nvalid.append(valid.sum(axis=0))
        years_all.append(int(y))
    ds.close()
counts = np.array(counts, dtype=np.float32)
nvalid = np.array(nvalid)
years_all = np.array(years_all)
ok = nvalid >= 355
counts = np.where(ok, counts, np.nan)

out_ds = xr.Dataset(
    {"count": (("year", "latitude", "longitude"), counts),
     "land_mask": (("latitude", "longitude"), land)},
    coords={"year": years_all, "latitude": lats, "longitude": lons})
out_ds.to_netcdf(f"{BASE}/data/berkeley/tx95p_counts.nc",
                 encoding={"count": {"zlib": True, "complevel": 4}})

# ---------- region masks ----------
REGIONS = {
    "Northwest": ["Idaho", "Oregon", "Washington"],
    "N. Rockies & Plains": ["Montana", "Nebraska", "North Dakota",
                            "South Dakota", "Wyoming"],
    "Upper Midwest": ["Iowa", "Michigan", "Minnesota", "Wisconsin"],
    "West": ["California", "Nevada"],
    "Southwest": ["Arizona", "Colorado", "New Mexico", "Utah"],
    "Ohio Valley": ["Illinois", "Indiana", "Kentucky", "Missouri", "Ohio",
                    "Tennessee", "West Virginia"],
    "South": ["Arkansas", "Kansas", "Louisiana", "Mississippi", "Oklahoma",
              "Texas"],
    "Southeast": ["Alabama", "Florida", "Georgia", "North Carolina",
                  "South Carolina", "Virginia"],
    "Northeast": ["Connecticut", "Delaware", "Maine", "Maryland",
                  "Massachusetts", "New Hampshire", "New Jersey", "New York",
                  "Pennsylvania", "Rhode Island", "Vermont"],
}
S2R = {s: r for r, ss in REGIONS.items() for s in ss}
gj = json.load(open(f"{BASE}/data/us-states.json"))
lon2, lat2 = np.meshgrid(lons, lats)
pts = np.column_stack([lon2.ravel(), lat2.ravel()])
region_idx = np.full(len(pts), -1)
rnames = list(REGIONS)
for f in gj["features"]:
    nm = f["properties"]["name"]
    if nm not in S2R:
        continue
    ridx = rnames.index(S2R[nm])
    geom = f["geometry"]
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for poly in polys:
        region_idx[MplPath(np.array(poly[0])).contains_points(pts)] = ridx
region_grid = region_idx.reshape(lat2.shape)

# ---------- aggregate ----------
coslat = np.cos(np.deg2rad(lats))[:, None] * np.ones_like(land)
w_base = coslat * land
res = pd.DataFrame({"year": years_all}).set_index("year")

def wmean(mask):
    w = w_base * mask
    num = np.nansum(counts * w[None], axis=(1, 2))
    den = np.array([(w * np.isfinite(counts[i])).sum() for i in range(len(counts))])
    return num / den

res["CONUS"] = wmean((region_grid >= 0).astype(float))
for i, r in enumerate(rnames):
    res[r] = wmean((region_grid == i).astype(float))
res.round(2).to_csv(f"{BASE}/results/be_tx95p_annual.csv")

print("\n1930s vs 2000-2023 (days > local 95th pct, base 1961-1990 ~18.3/yr):")
print(f"{'region':22s} {'1930s':>7s} {'2000-23':>8s} {'2014-23':>8s} ratio30s peak")
for c in res.columns:
    s = res[c].dropna()
    d30 = s.loc[1930:1939].mean()
    rec = s.loc[2000:2023].mean()
    dec = s.loc[2014:2023].mean()
    print(f"{c:22s} {d30:7.2f} {rec:8.2f} {dec:8.2f} {d30/rec:5.2f}  "
          f"{int(s.idxmax())} ({s.max():.1f})")
