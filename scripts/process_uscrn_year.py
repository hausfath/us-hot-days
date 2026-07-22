"""Download one year of USCRN hourly data (CONUS stations), compute per-station
annual counts of days >= 95F under each of 24 simulated observation hours
(max-thermometer window: 24 hours ending at obs hour, attributed to that day;
hour 0 = true calendar day). Appends to results/uscrn_tobs_counts.csv, deletes
raw files.

Usage: python3 process_uscrn_year.py 2015
"""
import io
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import requests

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days"
URL = "https://www.ncei.noaa.gov/pub/data/uscrn/products/hourly02/{y}/"
T95 = 35.0
CONUS = set("AL AZ AR CA CO CT DE FL GA ID IL IN IA KS KY LA ME MD MA MI MN MS "
            "MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA "
            "WA WV WI WY".split())

year = int(sys.argv[1])
out_csv = f"{BASE}/results/uscrn_tobs_counts.csv"

listing = requests.get(URL.format(y=year), timeout=60).text
files = sorted(set(re.findall(rf"CRNH0203-{year}-[^\"]*?\.txt", listing)))
files = [f for f in files if f.split("-")[2][:2] in CONUS]
print(f"{year}: {len(files)} CONUS station files", flush=True)

def fetch(fn):
    r = requests.get(URL.format(y=year) + fn, timeout=120)
    r.raise_for_status()
    return fn, r.text

rows = []
with ThreadPoolExecutor(max_workers=8) as ex:
    for fn, text in ex.map(fetch, files):
        name = fn.replace(f"CRNH0203-{year}-", "").replace(".txt", "")
        df = pd.read_csv(io.StringIO(text), sep=r"\s+", header=None,
                         usecols=[3, 4, 6, 7, 10],
                         names=["lst_date", "lst_time", "lon", "lat", "tmax"])
        df = df[(df.tmax > -100) & (df.tmax < 60)]
        if df.empty:
            continue
        ts = pd.to_datetime(df.lst_date.astype(str), format="%Y%m%d") + \
             pd.to_timedelta(df.lst_time // 100, unit="h")
        # t_end: hour ending at this clock time; LST_TIME 0000 ends at 00:00
        s = pd.Series(df.tmax.values, index=ts).sort_index()
        s = s[~s.index.duplicated()]

        # completeness: valid Apr-Oct hours this calendar year
        warm = s[(s.index.year == year) & (s.index.month >= 4) & (s.index.month <= 10)]
        n_warm = len(warm)

        # for each obs hour H: daily reading d = max of hours with
        # t_end in (d-1 H:00, d H:00]  ->  shift by (24-H) hours then group by date
        counts = {}
        for H in range(24):
            shifted = s.copy()
            shifted.index = shifted.index + pd.Timedelta(hours=23 - H) + \
                pd.Timedelta(minutes=59)
            daily = shifted.groupby(shifted.index.date).max()
            dyear = pd.Series(daily.values,
                              index=pd.to_datetime(list(daily.index)))
            dyear = dyear[dyear.index.year == year]
            counts[H] = int((dyear >= T95).sum())
        rows.append({"station": name, "year": year,
                     "lon": df.lon.iloc[0], "lat": df.lat.iloc[0],
                     "n_warm_hours": n_warm,
                     **{f"h{H}": counts[H] for H in range(24)}})

res = pd.DataFrame(rows)
header = not os.path.exists(out_csv)
res.to_csv(out_csv, mode="a", header=header, index=False)
print(f"{year}: wrote {len(res)} stations", flush=True)
