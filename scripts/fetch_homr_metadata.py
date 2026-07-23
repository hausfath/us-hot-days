"""Fetch HOMR equipment histories for all USHCN stations; extract TEMP
equipment periods. Output: results/ushcn_equipment.csv with one row per
station-period (coop_id, begin, end, equipment)."""
import json
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days"

st = pd.read_fwf(f"{BASE}/data/ushcn/ushcn-v2.5-stations.txt", header=None,
                 colspecs=[(0, 11), (12, 20), (21, 30), (31, 37), (38, 40), (41, 71)],
                 names=["id", "lat", "lon", "elev", "state", "name"])
st["coop"] = st.id.str[-6:]
print(f"{len(st)} USHCN stations")

def fetch(coop):
    try:
        r = requests.get(
            "https://www.ncei.noaa.gov/access/homr/services/station/search",
            params={"qid": f"COOP:{coop}", "date": "all"}, timeout=60)
        if r.status_code != 200:
            return coop, []
        rows = []
        for stn in r.json().get("stationCollection", {}).get("stations", []):
            for e in stn.get("elements", []):
                if e.get("element") == "TEMP":
                    eq = (e.get("equipment") or {}).get("equipment", "")
                    dt = e.get("date", {})
                    rows.append((dt.get("beginDate", "")[:10],
                                 dt.get("endDate", "")[:10], eq))
        return coop, sorted(set(rows))
    except Exception:
        return coop, []

out = []
done = 0
with ThreadPoolExecutor(max_workers=8) as ex:
    for coop, rows in ex.map(fetch, st.coop):
        for b, e, eq in rows:
            out.append({"coop": coop, "begin": b, "end": e, "equipment": eq})
        done += 1
        if done % 100 == 0:
            print(f"{done} stations fetched", flush=True)

df = pd.DataFrame(out)
df.to_csv(f"{BASE}/results/ushcn_equipment.csv", index=False)
print(f"wrote {len(df)} equipment periods for "
      f"{df.coop.nunique() if len(df) else 0} stations")
