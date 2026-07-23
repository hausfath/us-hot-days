"""Per-station p95 exceedance counts from GHCN daily TMax, raw and homogenized.

Raw: QC-filtered GHCN daily TMax as-is.
Homogenized: raw daily + USHCN monthly delta (FLs.52j - raw) for the station's
month (USHCN member stations only), i.e. daily data adjusted so monthly means
match NOAA's fully homogenized USHCN record.

For each variant, the station's p95 threshold is the 95th percentile of its
own 1961-1990 daily values (that variant), requiring >=7300 valid base days.
Outputs results/station_p95_counts.csv.
"""
import glob
import os

import numpy as np
import pandas as pd

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/p95_comparison"

deltas = pd.read_csv(f"{BASE}/data/ushcn/homog_deltas.csv.gz")
dmap = {}
for coop, g in deltas.groupby("coop"):
    dmap[f"{int(coop):06d}" if isinstance(coop, (int, np.integer)) else str(coop).zfill(6)] = \
        dict(zip(zip(g.year, g.month), g.delta))
print(f"USHCN delta stations: {len(dmap)}")

files = sorted(glob.glob(f"{BASE}/data/ghcn/stations/*.csv.gz"))
print(f"{len(files)} GHCN station files")

rows = []
n_ushcn = 0
for i, fp in enumerate(files):
    sid = os.path.basename(fp).replace(".csv.gz", "")
    coop = sid[-6:]
    try:
        df = pd.read_csv(fp, header=None, usecols=[0, 1, 2, 3, 5],
                         names=["id", "date", "elem", "value", "qflag"],
                         dtype={"date": str, "qflag": str})
    except Exception:
        continue
    df = df[(df.elem == "TMAX") & (df.qflag.isna())]
    if df.empty:
        continue
    tmax = df.value.values / 10.0
    year = df.date.str[:4].astype(int).values
    month = df.date.str[4:6].astype(int).values

    variants = {"raw": tmax}
    dd = dmap.get(coop)
    if dd is not None:
        adj = np.array([dd.get((y, m), np.nan) for y, m in zip(year, month)])
        homog = tmax + adj                       # NaN where no monthly delta
        variants["homog"] = homog
        n_ushcn += 1

    base_sel = (year >= 1961) & (year <= 1990)
    rec = {}
    for name, vals in variants.items():
        bv = vals[base_sel]
        bv = bv[np.isfinite(bv)]
        if len(bv) < 7300:
            rec[name] = None
            continue
        th = np.percentile(bv, 95)
        rec[name] = th
    warm = (month >= 4) & (month <= 10)
    g = pd.DataFrame({"year": year, "warm": warm})
    warm_days = g.groupby("year")["warm"].sum()

    for y in np.unique(year):
        sel = year == y
        row = {"id": sid, "coop": coop, "year": int(y),
               "warm_days": int(warm_days.loc[y])}
        for name, vals in variants.items():
            if rec.get(name) is None:
                row[f"n_{name}"] = np.nan
                row[f"nd_{name}"] = np.nan
                continue
            vv = vals[sel]
            vv = vv[np.isfinite(vv)]
            # count ties at the threshold as half-exceedances: GHCN tenths-degC
            # precision puts the percentile exactly on a tied value, and strict
            # > vs >= would bias raw and homogenized variants differently
            row[f"n_{name}"] = float((vv > rec[name]).sum()
                                     + 0.5 * (vv == rec[name]).sum())
            row[f"nd_{name}"] = int(len(vv))
        row["ushcn"] = dd is not None
        rows.append(row)
    if (i + 1) % 150 == 0:
        print(f"  {i+1} stations done", flush=True)

out = pd.DataFrame(rows)
out = out[(out.year >= 1890) & (out.year <= 2026)]
out.to_csv(f"{BASE}/results/station_p95_counts.csv", index=False)
print(f"wrote {len(out)} station-years; USHCN members processed: {n_ushcn}")
