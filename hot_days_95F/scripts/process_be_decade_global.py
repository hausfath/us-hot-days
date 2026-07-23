"""Download one BE daily TMAX decadal file, compute GLOBAL land annual counts of
days >= 95/100/105 F per 1x1 cell, save small netCDF, delete raw.

Usage: python3 process_be_decade_global.py 1890
"""
import os
import subprocess
import sys

import numpy as np
import xarray as xr

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/hot_days_95F"
URL = ("https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com/"
       "Global/Gridded/Complete_TMAX_Daily_LatLong1_{}.nc")
THRESH = {"95F": 35.0, "100F": (100 - 32) * 5 / 9, "105F": (105 - 32) * 5 / 9}

decade = int(sys.argv[1])
raw = f"{BASE}/data/berkeley/Complete_TMAX_Daily_LatLong1_{decade}.nc"
out = f"{BASE}/data/berkeley/global_counts_{decade}.nc"

if os.path.exists(out):
    print(f"{decade}: global counts exist, skipping", flush=True)
    sys.exit(0)

if not os.path.exists(raw):
    print(f"{decade}: downloading...", flush=True)
    subprocess.run(["curl", "-s", "-f", "--retry", "3", "-o", raw,
                    URL.format(decade)], check=True)

ds = xr.open_dataset(raw)
clim = ds["climatology"].load().values                     # (365, lat, lon)
years = ds["year"].load().values.astype(int)
doy = np.clip(ds["day_of_year"].load().values.astype(int), 1, 365)
year_list = np.unique(years)

nlat, nlon = clim.shape[1], clim.shape[2]
counts = np.zeros((len(THRESH), len(year_list), nlat, nlon), dtype=np.float32)
nvalid = np.zeros((len(year_list), nlat, nlon), dtype=np.int16)

# process one year at a time to keep memory modest
for iy, y in enumerate(year_list):
    idx = np.where(years == y)[0]
    anom = ds["temperature"].isel(time=slice(idx[0], idx[-1] + 1)).load().values
    absolute = anom + clim[doy[idx] - 1, :, :]
    valid = np.isfinite(absolute)
    nvalid[iy] = valid.sum(axis=0)
    for it, tc in enumerate(THRESH.values()):
        counts[it, iy] = (absolute >= tc).sum(axis=0, where=valid)
    del anom, absolute, valid

out_ds = xr.Dataset(
    {
        "count": (("threshold", "year", "latitude", "longitude"), counts),
        "ndays_valid": (("year", "latitude", "longitude"), nvalid),
        "land_mask": (("latitude", "longitude"), ds["land_mask"].load().values),
    },
    coords={
        "threshold": list(THRESH.keys()),
        "year": year_list,
        "latitude": ds.latitude.values,
        "longitude": ds.longitude.values,
    },
)
out_ds.to_netcdf(out, encoding={"count": {"zlib": True, "complevel": 4},
                                "ndays_valid": {"zlib": True, "complevel": 4}})
ds.close()
os.remove(raw)
print(f"{decade}: done, raw deleted", flush=True)
