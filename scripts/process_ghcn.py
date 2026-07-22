"""Compute per-station annual counts of days >= 95/100/105 F from GHCN-Daily TMAX.

QC: drop any observation with a non-blank quality flag.
Completeness bookkeeping: track valid TMAX days in Apr-Oct (when essentially all
CONUS >=95F days occur) so aggregation can screen incomplete station-years.
"""
import glob
import gzip
import os

import numpy as np
import pandas as pd

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days"
T95, T100, T105 = 35.0, (100 - 32) * 5 / 9, (105 - 32) * 5 / 9

files = sorted(glob.glob(f"{BASE}/data/ghcn/stations/*.csv.gz"))
print(f"{len(files)} station files")

rows = []
for i, fp in enumerate(files):
    sid = os.path.basename(fp).replace(".csv.gz", "")
    try:
        df = pd.read_csv(
            fp, header=None, usecols=[0, 1, 2, 3, 5],
            names=["id", "date", "elem", "value", "qflag"],
            dtype={"date": str, "qflag": str},
        )
    except Exception as e:
        print(f"  {sid}: READ FAIL {e}")
        continue
    df = df[(df.elem == "TMAX") & (df.qflag.isna())]
    if df.empty:
        continue
    tmax_c = df.value.values / 10.0
    year = df.date.str[:4].astype(int).values
    month = df.date.str[4:6].astype(int).values
    warm = (month >= 4) & (month <= 10)

    g = pd.DataFrame({
        "year": year,
        "n95": tmax_c >= T95,
        "n100": tmax_c >= T100,
        "n105": tmax_c >= T105,
        "warm_days": warm,
        "all_days": 1,
    }).groupby("year").sum()
    g["id"] = sid
    rows.append(g.reset_index())
    if (i + 1) % 100 == 0:
        print(f"  {i + 1} done", flush=True)

out = pd.concat(rows, ignore_index=True)
out = out[(out.year >= 1890) & (out.year <= 2026)]
out.to_csv(f"{BASE}/results/ghcn_station_annual_counts.csv", index=False)
print(f"Wrote {len(out)} station-years for {out.id.nunique()} stations")
