"""Angular-distance-weighted (ADW) gridding of station p95 counts to the 1-deg
CONUS grid, following the modified Shepard approach of HadEX3/GHCNDEX
(New et al 2000; Donat et al 2013; Dunn et al 2020):

  w_k = [exp(-d_k / DLS)]^m * (1 + A_k),  m = 4
  A_k = sum_l w_l (1 - cos(theta_kl)) / sum_l w_l   (angular isolation)

DLS = 1250 km (empirical e-folding of annual p95-count anomaly correlations).
Cells need >=3 contributing stations within the DLS, else masked that year.
Same matched USHCN station set and screens as the 2x2 aggregation.
"""
import numpy as np
import pandas as pd
import xarray as xr

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/p95_comparison"
DLS_KM = 1250.0
M_EXP = 4.0
MIN_STN = 3
Y0, Y1 = 1895, 2025
NY = Y1 - Y0 + 1

# ---------- stations (same screens as 2x2 version) ----------
c = pd.read_csv(f"{BASE}/results/station_p95_counts.csv")
meta = pd.read_fwf(f"{BASE}/data/ushcn/ushcn-v2.5-stations.txt", header=None,
                   colspecs=[(0, 11), (12, 20), (21, 30)],
                   names=["uid", "lat", "lon"])
meta["id"] = "USC00" + meta.uid.str[-6:]
c = c[(c.year >= Y0) & (c.year <= Y1) & c.ushcn]
c["valid"] = c.warm_days >= 172
hb = c.groupby("id").apply(lambda g: g.n_raw.notna().any() and g.n_homog.notna().any(),
                           include_groups=False)
nv = c[c.valid & c.id.isin(hb[hb].index)].groupby("id").year.nunique()
keep = nv[nv >= 0.85 * NY].index
df = c[c.id.isin(keep) & c.valid].merge(meta[["id", "lat", "lon"]], on="id")
df = df[df.n_raw.notna() & df.n_homog.notna()]
df["n_raw"] = df.n_raw * 365.25 / df.nd_raw
df["n_homog"] = df.n_homog * 365.25 / df.nd_homog
sids = sorted(df.id.unique())
sidx = {s: k for k, s in enumerate(sids)}
S = len(sids)
print(f"stations: {S}")
slat = meta.set_index("id").loc[sids, "lat"].values
slon = meta.set_index("id").loc[sids, "lon"].values

# station-year matrices
years = np.arange(Y0, Y1 + 1)
NR = np.full((NY, S), np.nan)
NH = np.full((NY, S), np.nan)
for _, r in df.iterrows():
    NR[int(r.year) - Y0, sidx[r.id]] = r.n_raw
    NH[int(r.year) - Y0, sidx[r.id]] = r.n_homog

# ---------- grid geometry ----------
mask = xr.open_dataset(f"{BASE}/../hot_days_95F/data/conus_mask_1deg.nc").in_conus
glat, glon = np.meshgrid(mask.latitude.values, mask.longitude.values, indexing="ij")
gm = mask.values > 0
cells = np.column_stack([glat[gm], glon[gm]])
G = len(cells)
print(f"grid cells: {G}")

def hav_km(la1, lo1, la2, lo2):
    la1, lo1, la2, lo2 = map(np.radians, [la1, lo1, la2, lo2])
    return 6371 * 2 * np.arcsin(np.sqrt(
        np.sin((la2 - la1) / 2) ** 2 +
        np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2))

# distance and bearing from each cell to each station
D = np.zeros((G, S))
TH = np.zeros((G, S))
for g in range(G):
    D[g] = hav_km(cells[g, 0], cells[g, 1], slat, slon)
    dlon = np.radians(slon - cells[g, 1])
    y = np.sin(dlon) * np.cos(np.radians(slat))
    x = (np.cos(np.radians(cells[g, 0])) * np.sin(np.radians(slat)) -
         np.sin(np.radians(cells[g, 0])) * np.cos(np.radians(slat)) * np.cos(dlon))
    TH[g] = np.arctan2(y, x)
W0 = np.exp(-M_EXP * D / DLS_KM)
W0[D > DLS_KM] = 0.0

def grid_year(vals):
    """ADW field for one year's station values (with NaNs)."""
    ok = np.isfinite(vals)
    field = np.full(G, np.nan)
    for g in range(G):
        w = W0[g] * ok
        use = w > 1e-6
        if use.sum() < MIN_STN:
            continue
        wk = w[use]
        th = TH[g][use]
        # angular isolation term
        A = np.empty(len(wk))
        sw = wk.sum()
        for k in range(len(wk)):
            A[k] = (wk * (1 - np.cos(th - th[k]))).sum() / sw
        wk = wk * (1 + A)
        field[g] = (wk * vals[use]).sum() / wk.sum()
    return field

wcell = np.cos(np.deg2rad(cells[:, 0]))
rows = []
for i, y in enumerate(years):
    fr = grid_year(NR[i])
    fh = grid_year(NH[i])
    okr = np.isfinite(fr)
    rows.append({"year": int(y),
                 "ghcn_raw_adw": float(np.nansum(fr * wcell) / wcell[okr].sum()),
                 "ghcn_homog_adw": float(np.nansum(fh * wcell) / wcell[np.isfinite(fh)].sum()),
                 "cells_covered": int(okr.sum())})
    if y % 20 == 0:
        print(f"  {y}: {okr.sum()}/{G} cells", flush=True)

res = pd.DataFrame(rows).set_index("year")
res.round(3).to_csv(f"{BASE}/results/conus_p95_stations_adw.csv")
print(f"\ncoverage: min {res.cells_covered.min()}/{G} cells")
for v in ["ghcn_raw_adw", "ghcn_homog_adw"]:
    s = res[v]
    print(f"{v}: 1930s={s.loc[1930:1939].mean():.2f}  1961-90={s.loc[1961:1990].mean():.2f}  "
          f"2000-23={s.loc[2000:2023].mean():.2f}")
