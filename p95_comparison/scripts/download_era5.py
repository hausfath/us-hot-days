"""Download ERA5 daily-maximum 2m temperature over CONUS, one file per year.

Uses the CDS 'derived-era5-single-levels-daily-statistics' dataset with the
daily max computed in UTC-06:00 (CONUS-centered local days). Credentials come
from ~/.cdsapirc (never stored in this repo).

Usage: python3 download_era5.py 1960 2025
"""
import os
import sys

import cdsapi

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/p95_comparison"
y0, y1 = int(sys.argv[1]), int(sys.argv[2])

def _retrieve(c, year, out):
    c.retrieve(
        "derived-era5-single-levels-daily-statistics",
        {
            "product_type": "reanalysis",
            "variable": ["2m_temperature"],
            "year": str(year),
            "month": [f"{m:02d}" for m in range(1, 13)],
            "day": [f"{d:02d}" for d in range(1, 32)],
            "daily_statistic": "daily_maximum",
            "time_zone": "utc-06:00",
            "frequency": "1_hourly",
            "area": [50, -126, 24, -66],
        },
        out,
    )

c = cdsapi.Client(quiet=True)
for year in range(y0, y1 + 1):
    out = f"{BASE}/data/era5/raw/tmax_{year}.nc"
    if os.path.exists(out) and os.path.getsize(out) > 1e6:
        print(f"{year}: exists, skipping", flush=True)
        continue
    print(f"{year}: requesting...", flush=True)
    ok = False
    for attempt in range(10):
        try:
            _retrieve(c, year, out)
            ok = True
            break
        except Exception as e:
            wait = min(120 * (attempt + 1), 900)
            print(f"{year}: attempt {attempt+1} failed ({str(e)[:80]}); "
                  f"retrying in {wait}s", flush=True)
            import time; time.sleep(wait)
    if not ok:
        print(f"{year}: GIVING UP", flush=True)
        continue
    print(f"{year}: saved {os.path.getsize(out)/1e6:.0f} MB", flush=True)
print("ERA5 DONE", flush=True)
