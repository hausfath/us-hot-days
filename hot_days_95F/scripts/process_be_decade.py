"""Download one Berkeley Earth daily TMAX decadal file, compute annual counts of
days >= 95/100/105 F for each CONUS-box 1x1 cell, save small netCDF, delete raw.

Usage: python3 process_be_decade.py 1890
"""
import os
import subprocess
import sys

import numpy as np
import xarray as xr

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/hot_days_95F"
URL = ("https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com/"
       "Global/Gridded/Complete_TMAX_Daily_LatLong1_{}.nc")

# thresholds in deg C: 95F, 100F, 105F
THRESH = {"95F": 35.0, "100F": (100 - 32) * 5 / 9, "105F": (105 - 32) * 5 / 9}

LAT_SLICE = slice(24.0, 50.0)
LON_SLICE = slice(-126.0, -66.0)

decade = int(sys.argv[1])
raw = f"{BASE}/data/berkeley/Complete_TMAX_Daily_LatLong1_{decade}.nc"
out = f"{BASE}/data/berkeley/counts_{decade}.nc"

if os.path.exists(out):
    print(f"{decade}: counts exist, skipping")
    sys.exit(0)

if not os.path.exists(raw):
    print(f"{decade}: downloading...", flush=True)
    subprocess.run(["curl", "-s", "-f", "-o", raw, URL.format(decade)], check=True)

ds = xr.open_dataset(raw)
sub = ds[["temperature", "climatology", "year", "day_of_year", "land_mask"]].sel(
    latitude=LAT_SLICE, longitude=LON_SLICE
)
anom = sub["temperature"].load()            # (time, lat, lon)
clim = sub["climatology"].load()            # (day_number 1..365, lat, lon)
years = sub["year"].values.astype(int)
doy = sub["day_of_year"].values.astype(int)
doy = np.clip(doy, 1, 365)                  # map leap day 366 onto 365

# absolute TMAX = anomaly + climatology for that day of year
absolute = anom.values + clim.values[doy - 1, :, :]

year_list = np.unique(years)
nlat, nlon = anom.shape[1], anom.shape[2]
counts = np.full((len(THRESH), len(year_list), nlat, nlon), np.nan, dtype=np.float32)
nvalid = np.zeros((len(year_list), nlat, nlon), dtype=np.int16)

for iy, y in enumerate(year_list):
    sel = years == y
    block = absolute[sel]                   # (ndays, lat, lon)
    valid = np.isfinite(block)
    nvalid[iy] = valid.sum(axis=0)
    for it, (name, tc) in enumerate(THRESH.items()):
        counts[it, iy] = (block >= tc).sum(axis=0, where=valid)

out_ds = xr.Dataset(
    {
        "count": (("threshold", "year", "latitude", "longitude"), counts),
        "ndays_valid": (("year", "latitude", "longitude"), nvalid),
        "land_mask": (("latitude", "longitude"), sub["land_mask"].values),
    },
    coords={
        "threshold": list(THRESH.keys()),
        "year": year_list,
        "latitude": anom.latitude.values,
        "longitude": anom.longitude.values,
    },
)
out_ds.to_netcdf(out)
ds.close()
os.remove(raw)
print(f"{decade}: done, years {year_list.min()}-{year_list.max()}, raw deleted", flush=True)
