"""Build per-station monthly homogenization adjustments for USHCN stations:
delta(station, year, month) = FLs.52j - raw monthly TMax (degC).
Applying these to raw GHCN daily TMax gives a daily series whose monthly means
match the fully homogenized (TOBs + pairwise breakpoint) USHCN record.

Output: data/ushcn/homog_deltas.parquet (coop id -> GHCN daily id mapping via
USHCN id: USH00xxxxxx <-> GHCN USC00xxxxxx or USW000xxxxx per station list).
"""
import glob

import numpy as np
import pandas as pd

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/p95_comparison"
VDIR = sorted(glob.glob(f"{BASE}/data/ushcn/ushcn.v2.5.5.*"))[-1]

def read_monthly(fp):
    rows = []
    for line in open(fp):
        year = int(line[12:16])
        for m in range(12):
            v = int(line[16 + 9 * m: 22 + 9 * m])
            if v != -9999:
                rows.append((year, m + 1, v / 100.0))
    return rows

out = []
files_f = sorted(glob.glob(f"{VDIR}/*.FLs.52j.tmax"))
for ff in files_f:
    sid = ff.split("/")[-1][:11]
    fr = f"{VDIR}/{sid}.raw.tmax"
    try:
        fl = {(y, m): v for y, m, v in read_monthly(ff)}
        rw = {(y, m): v for y, m, v in read_monthly(fr)}
    except FileNotFoundError:
        continue
    for k in fl:
        if k in rw:
            out.append({"ushcn": sid, "year": k[0], "month": k[1],
                        "delta": round(fl[k] - rw[k], 2)})

df = pd.DataFrame(out)
df["coop"] = df.ushcn.str[-6:]
df.to_csv(f"{BASE}/data/ushcn/homog_deltas.csv.gz", index=False)
print(f"{df.ushcn.nunique()} stations, {len(df)} station-months")
print("delta stats (degC):")
print(df.delta.describe().round(3).to_string())
# how big are adjustments by era?
df["dec"] = df.year // 10 * 10
print("\nmean delta by decade (should trend toward 0 in recent years):")
print(df[df.dec >= 1890].groupby("dec").delta.mean().round(3).to_string())
