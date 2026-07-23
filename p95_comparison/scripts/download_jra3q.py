"""Harvest JRA-3Q daily TMax over CONUS via NCSS monthly subsets.

Source: NCAR GDEX d640000, product minmax_surf, variable tmpmax2m (hourly max
2m temperature, native ~0.375 deg Gaussian grid), anonymous NCSS access.
For each month: request CONUS bbox, shift times UTC-6, take daily max over
local days, append to a compact per-year netCDF. License: CC-BY-NC-SA 4.0.

Usage: python3 download_jra3q.py 1960 2025
"""
import calendar
import io
import os
import sys
import time

import numpy as np
import pandas as pd
import requests
import xarray as xr

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/p95_comparison"
OUT = f"{BASE}/data/jra3q"
os.makedirs(OUT, exist_ok=True)

NCSS = ("https://tds.gdex.ucar.edu/thredds/ncss/grid/files/g/d640000/minmax_surf/"
        "{ym}/jra3q.minmax_surf.0_0_0.tmpmax2m-hgt-fc-gauss.{ym}0100_{ym}{eday}23.nc"
        "?var=tmpmax2m-hgt-fc-gauss&north=50.5&south=23.5&west=-126.5&east=-65.5"
        "&accept=netcdf&temporal=all")

y0, y1 = int(sys.argv[1]), int(sys.argv[2])
for year in range(y0, y1 + 1):
    out = f"{OUT}/tmax_daily_{year}.nc"
    if os.path.exists(out):
        print(f"{year}: exists", flush=True)
        continue
    monthly = []
    fail = False
    for m in range(1, 13):
        ym = f"{year}{m:02d}"
        eday = calendar.monthrange(year, m)[1]
        url = NCSS.format(ym=ym, eday=eday)
        ok = False
        for attempt in range(6):
            try:
                r = requests.get(url, timeout=300)
                r.raise_for_status()
                ds = xr.open_dataset(io.BytesIO(r.content))
                ok = True
                break
            except Exception as e:
                time.sleep(20 * (attempt + 1))
        if not ok:
            print(f"{ym}: FAILED", flush=True)
            fail = True
            break
        var = [v for v in ds.data_vars if v.startswith("tmpmax2m")][0]
        da = ds[var].load()
        # hourly max fields, times in UTC; shift to local (UTC-6) days
        t_local = pd.to_datetime(da.time.values) - pd.Timedelta(hours=6)
        da = da.assign_coords(time=t_local)
        daily = da.groupby(da.time.dt.floor("D")).max()
        daily = daily.rename({"floor": "date"} if "floor" in daily.dims else
                             {daily.dims[0]: "date"})
        monthly.append(daily)
        ds.close()
        time.sleep(1)
    if fail:
        continue
    yr = xr.concat(monthly, dim="date")
    # month-boundary duplicate local days: keep max
    yr = yr.groupby("date").max()
    yr = yr.sel(date=str(year))
    yr.name = "tmax"
    enc = {"tmax": {"zlib": True, "complevel": 4}}
    yr.to_dataset().to_netcdf(out, encoding=enc)
    print(f"{year}: saved {os.path.getsize(out)/1e6:.1f} MB "
          f"({yr.sizes['date']} days)", flush=True)
print("JRA3Q DONE", flush=True)
