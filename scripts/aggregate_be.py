"""Aggregate Berkeley Earth per-cell hot-day counts to CONUS annual averages.

Weight = cos(lat) * land_mask * in_conus. Also computes the average over only
the 2x2 cells used in the GHCN analysis, for an apples-to-apples domain check.
"""
import glob

import numpy as np
import pandas as pd
import xarray as xr

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days"

files = sorted(glob.glob(f"{BASE}/data/berkeley/counts_*.nc"))
ds = xr.concat(
    [xr.open_dataset(f)[["count", "ndays_valid"]].load() for f in files],
    dim="year",
)
print(f"Years: {int(ds.year.min())}-{int(ds.year.max())}")

mask = xr.open_dataset(f"{BASE}/data/conus_mask_1deg.nc").in_conus
land = xr.open_dataset(files[0]).land_mask

w = np.cos(np.deg2rad(ds.latitude)) * land * mask
w = w.broadcast_like(ds["count"].isel(threshold=0, year=0))

# require near-complete years in each cell (BE fields can end mid-year)
complete = ds.ndays_valid >= 355
cnt = ds["count"].where(complete)

num = (cnt * w).sum(["latitude", "longitude"])
den = w.where(complete).sum(["latitude", "longitude"])
conus = (num / den).to_dataset(dim="threshold").to_dataframe().reset_index()
conus["frac_domain"] = (den.isel(threshold=0) / w.sum()).values if "threshold" in den.dims else (den / w.sum()).values

conus.to_csv(f"{BASE}/results/be_conus_annual.csv", index=False)
print(conus.tail(6).round(2).to_string(index=False))

# GHCN-cell-matched domain: average BE 1-deg cells falling in the GHCN 2x2 cells
gh = pd.read_csv(f"{BASE}/results/ghcn_conus_annual.csv")  # noqa: F841 (existence check)
cell_list = pd.read_csv(f"{BASE}/results/ghcn_cells_used.csv")
sel = xr.zeros_like(mask)
for _, r in cell_list.iterrows():
    sel.loc[dict(latitude=slice(r.latbin - 1, r.latbin + 1),
                 longitude=slice(r.lonbin - 1, r.lonbin + 1))] = 1
w2 = np.cos(np.deg2rad(ds.latitude)) * land * mask * sel
w2 = w2.broadcast_like(ds["count"].isel(threshold=0, year=0))
num2 = (cnt * w2).sum(["latitude", "longitude"])
den2 = w2.where(complete).sum(["latitude", "longitude"])
matched = (num2 / den2).to_dataset(dim="threshold").to_dataframe().reset_index()
matched.to_csv(f"{BASE}/results/be_conus_annual_ghcn_domain.csv", index=False)
print("wrote GHCN-domain-matched BE series")
