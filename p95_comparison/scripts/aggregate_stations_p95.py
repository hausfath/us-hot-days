"""Aggregate per-station p95 exceedance counts to CONUS series for the
matched USHCN station set (raw and homogenized on identical stations).

Screens: station-year valid if >=80% of Apr-Oct days observed (warm_days>=172);
station kept if valid in >=85% of years 1895-2025 AND has thresholds for both
variants. 2x2 deg gridding, cells present >=95% of years, cos(lat) weights.
"""
import numpy as np
import pandas as pd

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/p95_comparison"
Y0, Y1 = 1895, 2025
NY = Y1 - Y0 + 1

c = pd.read_csv(f"{BASE}/results/station_p95_counts.csv")
meta = pd.read_fwf(f"{BASE}/data/ushcn/ushcn-v2.5-stations.txt", header=None,
                   colspecs=[(0, 11), (12, 20), (21, 30)],
                   names=["uid", "lat", "lon"])
meta["id"] = "USC00" + meta.uid.str[-6:]
meta = meta[["id", "lat", "lon"]]

c = c[(c.year >= Y0) & (c.year <= Y1) & c.ushcn]
c["valid"] = c.warm_days >= 172
# both variants must exist for the station (paired comparison)
has_both = c.groupby("id").apply(
    lambda g: g.n_raw.notna().any() and g.n_homog.notna().any(),
    include_groups=False)
paired_ids = has_both[has_both].index
nv = c[c.valid & c.id.isin(paired_ids)].groupby("id").year.nunique()
keep = nv[nv >= 0.85 * NY].index
print(f"USHCN stations paired+screened: {len(keep)}")

df = c[c.id.isin(keep) & c.valid].merge(meta, on="id", how="inner")
print(f"with coordinates: {df.id.nunique()}")
# strict pairing: a station-year counts only if BOTH variants have data;
# scale counts for missing days (count * 365.25/valid_days per variant)
df = df[df.n_raw.notna() & df.n_homog.notna()]
df["n_raw"] = df.n_raw * 365.25 / df.nd_raw
df["n_homog"] = df.n_homog * 365.25 / df.nd_homog
df["latbin"] = (np.floor((df.lat - 24) / 2) * 2 + 25).astype(int)
df["lonbin"] = (np.floor((df.lon + 126) / 2) * 2 - 125).astype(int)

cell = df.groupby(["latbin", "lonbin", "year"])[["n_raw", "n_homog"]].mean().reset_index()
cover = cell.groupby(["latbin", "lonbin"]).year.nunique()
good = cover[cover >= 0.95 * NY].index
cell = cell.set_index(["latbin", "lonbin"]).loc[good].reset_index()
print(f"grid cells: {len(good)}")
cell["w"] = np.cos(np.deg2rad(cell.latbin))

out = []
for y, g in cell.groupby("year"):
    w = g.w / g.w.sum()
    out.append({"year": y,
                "ghcn_raw": (g.n_raw * w).sum(),
                "ghcn_homog": (g.n_homog * w).sum(),
                "n_cells": len(g)})
res = pd.DataFrame(out).set_index("year")
res.round(3).to_csv(f"{BASE}/results/conus_p95_stations.csv")

for v in ["ghcn_raw", "ghcn_homog"]:
    s = res[v]
    print(f"\n{v}: 1930s={s.loc[1930:1939].mean():.2f}  "
          f"1961-90={s.loc[1961:1990].mean():.2f}  "
          f"2000-23={s.loc[2000:2023].mean():.2f}  2014-23={s.loc[2014:2023].mean():.2f}")
