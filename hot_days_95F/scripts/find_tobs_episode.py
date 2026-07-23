"""Find a clean, real double-count episode for the artifact mechanism panel:
a hot afternoon that a 5 PM observer logs as TWO days >=95F but which the true
calendar record counts once. Extracts a 72-hour hourly trace for embedding.

Usage: python3 find_tobs_episode.py STATION_NAME YEAR   (e.g. KS_Manhattan_6_SSW 2012)
"""
import io
import json
import sys

import pandas as pd
import requests

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/hot_days_95F"
URL = "https://www.ncei.noaa.gov/pub/data/uscrn/products/hourly02/{y}/CRNH0203-{y}-{s}.txt"
T95 = 35.0

station, year = sys.argv[1], int(sys.argv[2])
txt = requests.get(URL.format(y=year, s=station), timeout=120).text
df = pd.read_csv(io.StringIO(txt), sep=r"\s+", header=None,
                 usecols=[3, 4, 10], names=["lst_date", "lst_time", "tmax"])
df = df[(df.tmax > -100) & (df.tmax < 60)]
ts = pd.to_datetime(df.lst_date.astype(str), format="%Y%m%d") + \
     pd.to_timedelta(df.lst_time // 100, unit="h")
s = pd.Series(df.tmax.values, index=ts).sort_index()
s = s[~s.index.duplicated()]

# true calendar-day max: hours ending 01..24 belong to the day containing t_end-1min
cal = s.copy(); cal.index = cal.index - pd.Timedelta(minutes=1)
true_daily = cal.groupby(cal.index.date).max()

# 5PM observer: window ends 17:00, attributed to that day
obs = s.copy(); obs.index = obs.index + pd.Timedelta(hours=23 - 17, minutes=59)
obs_daily = obs.groupby(obs.index.date).max()

td = pd.Series(true_daily); od = pd.Series(obs_daily)
cands = []
for i in range(1, len(od) - 1):
    day, nxt = od.index[i], od.index[i + 1]
    prv = od.index[i - 1]
    if day not in td.index or nxt not in td.index or prv not in td.index:
        continue
    # isolated hot day: cool day before AND after, but 5PM observer logs
    # both the hot day and the following day as >=95
    if (od[day] >= T95 and od[nxt] >= T95 and td[day] >= T95
            and td[nxt] < 34.0 and td[prv] < 34.0):
        gap = od[nxt] - td[nxt]
        cands.append((gap, day, td[day], td[nxt], od[day], od[nxt]))
cands.sort(reverse=True)
print(f"{station} {year}: {len(cands)} double-count episodes")
for g, day, t1, t2, o1, o2 in cands[:6]:
    print(f"  {day}: true {t1:.1f}/{t2:.1f}C, 5PM-observer {o1:.1f}/{o2:.1f}C, gap {g:.1f}C")

if cands and len(sys.argv) > 3 and sys.argv[3] == "extract":
    _, day, *_ = cands[0]
    t0 = pd.Timestamp(day) - pd.Timedelta(days=1)
    win = s[(s.index > t0) & (s.index <= t0 + pd.Timedelta(hours=72))]
    out = {"station": station, "start_date": str(day),
           "hours": [{"t": str(i), "c": round(float(v), 2)} for i, v in win.items()]}
    with open(f"{BASE}/results/tobs_episode.json", "w") as f:
        json.dump(out, f)
    print(f"extracted 72h from {t0}")
