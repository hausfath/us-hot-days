"""Download one BE daily TMAX decadal file, save the CONUS-box absolute daily
TMax subset (climatology + anomaly) as compressed netCDF, delete the raw file.

Usage: python3 extract_be_conus_daily.py 1890
"""
import os
import subprocess
import sys

import numpy as np
import xarray as xr

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/hot_days_95F"
URL = ("https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com/"
       "Global/Gridded/Complete_TMAX_Daily_LatLong1_{}.nc")

decade = int(sys.argv[1])
raw = f"{BASE}/data/berkeley/Complete_TMAX_Daily_LatLong1_{decade}.nc"
out = f"{BASE}/data/berkeley/conus_daily_{decade}.nc"

if os.path.exists(out):
    print(f"{decade}: subset exists, skipping", flush=True)
    sys.exit(0)
if not os.path.exists(raw):
    print(f"{decade}: downloading...", flush=True)
    subprocess.run(["curl", "-s", "-f", "--retry", "3", "-o", raw,
                    URL.format(decade)], check=True)

ds = xr.open_dataset(raw)
sub = ds.sel(latitude=slice(24.0, 50.0), longitude=slice(-126.0, -66.0))
anom = sub["temperature"].load()
clim = sub["climatology"].load().values
years = sub["year"].values.astype(int)
doy = np.clip(sub["day_of_year"].values.astype(int), 1, 365)
absolute = (anom.values + clim[doy - 1, :, :]).astype(np.float32)

out_ds = xr.Dataset(
    {"tmax": (("time", "latitude", "longitude"), absolute),
     "year": (("time",), years),
     "month": (("time",), sub["month"].values.astype(np.int16)),
     "land_mask": (("latitude", "longitude"), sub["land_mask"].values)},
    coords={"latitude": anom.latitude.values, "longitude": anom.longitude.values},
)
out_ds.to_netcdf(out, encoding={"tmax": {"zlib": True, "complevel": 4}})
ds.close()
os.remove(raw)
print(f"{decade}: subset saved, raw deleted", flush=True)
