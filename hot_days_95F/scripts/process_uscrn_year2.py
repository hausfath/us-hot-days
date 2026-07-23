"""Download one year of USCRN hourly data (CONUS), compute per-station annual
counts of days >= 95F under each of 24 simulated observation hours AND each of
5 instrument cold-bias levels (0, -0.25, -0.5, -0.75, -1.0 C, i.e. thresholds
35.0..36.0 C). Column h{H}_b{k}: obs hour H, bias level k*0.25 C.
Appends to results/uscrn_tobs_counts2.csv.

Usage: python3 process_uscrn_year2.py 2015
"""
import io
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import requests

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/hot_days_95F"
URL = "https://www.ncei.noaa.gov/pub/data/uscrn/products/hourly02/{y}/"
BIASES = [round(0.1 * k, 1) for k in range(11)]
CONUS = set("AL AZ AR CA CO CT DE FL GA ID IL IN IA KS KY LA ME MD MA MI MN MS "
            "MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA "
            "WA WV WI WY".split())

year = int(sys.argv[1])
out_csv = f"{BASE}/results/uscrn_tobs_counts3.csv"

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
                         usecols=[3, 4, 10],
                         names=["lst_date", "lst_time", "tmax"])
        df = df[(df.tmax > -100) & (df.tmax < 60)]
        if df.empty:
            continue
        ts = pd.to_datetime(df.lst_date.astype(str), format="%Y%m%d") + \
             pd.to_timedelta(df.lst_time // 100, unit="h")
        s = pd.Series(df.tmax.values, index=ts).sort_index()
        s = s[~s.index.duplicated()]
        warm = s[(s.index.year == year) & (s.index.month >= 4) & (s.index.month <= 10)]

        rec = {"station": name, "year": year, "n_warm_hours": len(warm)}
        for H in range(24):
            shifted = s.copy()
            shifted.index = shifted.index + pd.Timedelta(hours=23 - H, minutes=59)
            daily = shifted.groupby(shifted.index.date).max()
            dyear = pd.Series(daily.values, index=pd.to_datetime(list(daily.index)))
            dyear = dyear[dyear.index.year == year]
            for k, b in enumerate(BIASES):
                rec[f"h{H}_b{k}"] = int((dyear >= 35.0 + b).sum())
        rows.append(rec)

res = pd.DataFrame(rows)
res.to_csv(out_csv, mode="a", header=not os.path.exists(out_csv), index=False)
print(f"{year}: wrote {len(res)} stations", flush=True)
