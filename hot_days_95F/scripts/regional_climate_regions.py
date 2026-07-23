"""Days >=95F by NOAA's nine US climate regions (Karl & Koss 1984), from BE
gridded daily TMAX counts. Map + 3x3 small multiples."""
import glob
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/hot_days_95F"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 150})

REGIONS = {
    "Northwest": ["Idaho", "Oregon", "Washington"],
    "N. Rockies & Plains": ["Montana", "Nebraska", "North Dakota", "South Dakota",
                            "Wyoming"],
    "Upper Midwest": ["Iowa", "Michigan", "Minnesota", "Wisconsin"],
    "West": ["California", "Nevada"],
    "Southwest": ["Arizona", "Colorado", "New Mexico", "Utah"],
    "Ohio Valley": ["Illinois", "Indiana", "Kentucky", "Missouri", "Ohio",
                    "Tennessee", "West Virginia"],
    "South": ["Arkansas", "Kansas", "Louisiana", "Mississippi", "Oklahoma",
              "Texas"],
    "Southeast": ["Alabama", "Florida", "Georgia", "North Carolina",
                  "South Carolina", "Virginia"],
    "Northeast": ["Connecticut", "Delaware", "Maine", "Maryland", "Massachusetts",
                  "New Hampshire", "New Jersey", "New York", "Pennsylvania",
                  "Rhode Island", "Vermont"],
}
STATE_TO_REGION = {s: r for r, ss in REGIONS.items() for s in ss}

# ---- load BE counts ------------------------------------------------------------
files = sorted(glob.glob(f"{BASE}/data/berkeley/counts_*.nc"))
ds = xr.concat([xr.open_dataset(f)[["count", "ndays_valid"]].load() for f in files],
               dim="year").sel(year=slice(1895, 2023))
land = xr.open_dataset(files[0]).land_mask
cnt95 = ds["count"].sel(threshold="95F").where(ds.ndays_valid >= 355)

# ---- assign each 1-deg cell center to a state/region ---------------------------
d = json.load(open(f"{BASE}/data/us-states.json"))
lats, lons = ds.latitude.values, ds.longitude.values
lon2, lat2 = np.meshgrid(lons, lats)
pts = np.column_stack([lon2.ravel(), lat2.ravel()])
region_idx = np.full(len(pts), -1)
region_names = list(REGIONS)
for f in d["features"]:
    name = f["properties"]["name"]
    if name not in STATE_TO_REGION:
        continue
    ridx = region_names.index(STATE_TO_REGION[name])
    geom = f["geometry"]
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for poly in polys:
        inside = MplPath(np.array(poly[0])).contains_points(pts)
        region_idx[inside] = ridx
region_grid = region_idx.reshape(lat2.shape)

# ---- regional area-weighted series ---------------------------------------------
w_base = np.cos(np.deg2rad(ds.latitude)) * land
series, stats_rows = {}, []
for i, r in enumerate(region_names):
    m = xr.DataArray((region_grid == i).astype(float),
                     coords={"latitude": lats, "longitude": lons},
                     dims=("latitude", "longitude"))
    w = w_base * m
    num = (cnt95 * w).sum(["latitude", "longitude"])
    den = w.where(np.isfinite(cnt95)).sum(["latitude", "longitude"])
    s = (num / den).to_series()
    series[r] = s
    d30 = s.loc[1930:1939].mean()
    drec = s.loc[2000:2023].mean()
    dmax = s.idxmax()
    stats_rows.append([r, int((region_grid == i).sum()), d30, drec, d30 / drec,
                       int(dmax), s.max()])
    print(f"{r:22s} cells={stats_rows[-1][1]:3d} 1930s={d30:6.2f} "
          f"2000-23={drec:6.2f} ratio={d30/drec:5.2f} peak={int(dmax)} ({s.max():.1f})")
pd.DataFrame(series).to_csv(f"{BASE}/results/be_region_95F.csv")

# ---- figure: 3x3 small multiples ------------------------------------------------
fig, axes = plt.subplots(3, 3, figsize=(11, 8.5), sharex=True)
for ax, r in zip(axes.ravel(), region_names):
    s = series[r].dropna()
    sm = s.rolling(11, center=True, min_periods=8).mean()
    ax.plot(s.index, s.values, color="#f4a582", lw=0.7)
    ax.plot(sm.index, sm.values, color="#b2182b", lw=1.8)
    ax.set_title(r, fontsize=10, loc="left")
    ax.set_xlim(1894, 2026)
    ax.set_ylim(bottom=0)
for ax in axes[:, 0]:
    ax.set_ylabel("Days ≥95°F")
fig.suptitle("Days at or above 95°F by US climate region, 1895–2023\n"
             "Berkeley Earth daily TMAX (1°×1°, area-weighted); thin: annual, bold: 11-yr mean; note the different y-axes",
             fontsize=12)
fig.text(0.01, 0.005, "Regions: NOAA/NCEI US climate regions (Karl and Koss 1984). "
         "Chart: The Climate Brink", fontsize=8, color="0.4")
fig.tight_layout(rect=[0, 0.02, 1, 0.97])
fig.savefig(f"{BASE}/figures/fig5_regions_3x3.png", bbox_inches="tight")
print("figure written")
