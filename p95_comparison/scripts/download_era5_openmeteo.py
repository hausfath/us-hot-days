"""Fetch ERA5 daily TMax (temperature_2m_max, models=era5) from the Open-Meteo
archive API at the 819 CONUS 1-deg cell centers, 1960-2025, local-time days
(America/Chicago aggregation). One gzipped CSV per point; restartable.
"""
import gzip
import io
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
import xarray as xr

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/p95_comparison"
OUT = f"{BASE}/data/era5/openmeteo"
os.makedirs(OUT, exist_ok=True)

mask = xr.open_dataset(f"{BASE}/../hot_days_95F/data/conus_mask_1deg.nc").in_conus
glat, glon = np.meshgrid(mask.latitude.values, mask.longitude.values, indexing="ij")
pts = [(float(la), float(lo)) for la, lo in
       zip(glat[mask.values > 0], glon[mask.values > 0])]
# thin to a 2-deg lattice: Open-Meteo weights long calls heavily against its
# free-tier quota; ~205 points is still dense vs the ~1250 km decorrelation
pts = [(la, lo) for la, lo in pts
       if int(round(la - 24.5)) % 2 == 0 and int(round(lo + 125.5)) % 2 == 0]
print(f"{len(pts)} points (2-deg lattice)")

URL = ("https://archive-api.open-meteo.com/v1/archive?latitude={la}&longitude={lo}"
       "&start_date=1960-01-01&end_date=2025-12-31&daily=temperature_2m_max"
       "&models=era5&timezone=America%2FChicago")

def fetch(pt):
    la, lo = pt
    fn = f"{OUT}/p_{la:.1f}_{lo:.1f}.csv.gz"
    if os.path.exists(fn) and os.path.getsize(fn) > 10000:
        return "skip"
    for attempt in range(8):
        try:
            r = requests.get(URL.format(la=la, lo=lo), timeout=120)
            if r.status_code == 429:
                time.sleep(30 * (attempt + 1))
                continue
            r.raise_for_status()
            d = r.json()["daily"]
            buf = io.StringIO()
            buf.write("date,tmax\n")
            for t, v in zip(d["time"], d["temperature_2m_max"]):
                buf.write(f"{t},{'' if v is None else v}\n")
            with gzip.open(fn, "wt") as f:
                f.write(buf.getvalue())
            return "ok"
        except Exception as e:
            time.sleep(10 * (attempt + 1))
    return "fail"

done = 0
with ThreadPoolExecutor(max_workers=2) as ex:
    for res in ex.map(fetch, pts):
        done += 1
        if done % 50 == 0:
            print(f"{done}/{len(pts)} ({res})", flush=True)
print("OPENMETEO DONE:",
      len([f for f in os.listdir(OUT) if f.endswith('.csv.gz')]), "files")
