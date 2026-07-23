"""MMTS transition bias via proximate-pair differencing.

For each USHCN station with a documented MMTS install date (HOMR) preceded by
non-MMTS equipment, pair it with nearby USHCN stations that had no documented
TEMP equipment change within +/-4 years. Difference their monthly anomalies
(TOB-adjusted data, so time-of-observation changes don't masquerade as
instrument steps) and measure the step at the documented date.

Outputs results/mmts_pairs.json for the artifact + printed summary.
"""
import glob
import json
import sys

import numpy as np
import pandas as pd

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days"
VERSION = sorted(glob.glob(f"{BASE}/data/ushcn/ushcn.v2.5.5.*"))[-1]
WIN = 48           # months each side
GAP = 2            # months excluded around the transition
MIN_MONTHS = 30    # valid diff months required each side
MAX_KM = 75.0
DATASET = sys.argv[1] if len(sys.argv) > 1 else "tob"   # tob | raw

# ---------- stations ----------
st = pd.read_fwf(f"{BASE}/data/ushcn/ushcn-v2.5-stations.txt", header=None,
                 colspecs=[(0, 11), (12, 20), (21, 30), (31, 37), (38, 40), (41, 71)],
                 names=["id", "lat", "lon", "elev", "state", "name"])
st["coop"] = st.id.str[-6:]
meta = st.set_index("coop")

# ---------- equipment histories ----------
eq = pd.read_csv(f"{BASE}/results/ushcn_equipment.csv",
                 dtype={"coop": str})
eq["begin"] = pd.to_datetime(eq.begin, errors="coerce")
eq = eq.dropna(subset=["begin"]).sort_values(["coop", "begin"])

events = {}      # coop -> list of (date, from_eq, to_eq) equipment-change events
first_mmts = {}  # coop -> (date, prior_equipment)
for coop, g in eq.groupby("coop"):
    g = g.drop_duplicates(subset=["begin", "equipment"]).sort_values("begin")
    prev = None
    evs = []
    for _, r in g.iterrows():
        if prev is not None and r.equipment != prev:
            evs.append((r.begin, prev, r.equipment))
        prev = r.equipment
    events[coop] = evs
    for d, frm, to in evs:
        if to == "MMTS" and frm != "MMTS":
            first_mmts[coop] = (d, frm)
            break

print(f"stations with equipment history: {len(events)}")
print(f"stations with documented non-MMTS -> MMTS transition: {len(first_mmts)}")
trans_years = pd.Series([d.year for d, _ in first_mmts.values()])
print("transition year distribution:")
print(trans_years.value_counts().sort_index().to_string())

# ---------- monthly data ----------
def load(var):
    rows = {}
    for fp in glob.glob(f"{VERSION}/*.{DATASET}.{var}"):
        sid = fp.split("/")[-1][:11]
        coop = sid[-6:]
        vals = {}
        for line in open(fp):
            year = int(line[12:16])
            for m in range(12):
                v = int(line[16 + 9 * m: 22 + 9 * m])
                if v != -9999:
                    vals[(year, m + 1)] = v / 100.0
        rows[coop] = vals
    return rows

print("loading monthly data...", flush=True)
tmax = load("tmax")
tmin = load("tmin")

def anom(series):
    """monthly anomalies vs station's own 1961-1990 monthly means"""
    clim = {}
    for m in range(1, 13):
        vv = [v for (y, mm), v in series.items() if mm == m and 1961 <= y <= 1990]
        if len(vv) >= 15:
            clim[m] = np.mean(vv)
    return {k: v - clim[k[1]] for k, v in series.items() if k[1] in clim}

print("computing anomalies...", flush=True)
tmax_a = {c: anom(s) for c, s in tmax.items()}
tmin_a = {c: anom(s) for c, s in tmin.items()}

def havkm(la1, lo1, la2, lo2):
    la1, lo1, la2, lo2 = map(np.radians, [la1, lo1, la2, lo2])
    return 6371 * 2 * np.arcsin(np.sqrt(
        np.sin((la2 - la1) / 2) ** 2 +
        np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2))

def month_index(d):
    return d.year * 12 + (d.month - 1)

def diff_step(cand, ref, t0i, data):
    """step in (cand - ref) anomaly difference at month index t0i"""
    pre, post, series = [], [], []
    for off in range(-WIN, WIN + 1):
        mi = t0i + off
        key = (mi // 12, mi % 12 + 1)
        a, b = data[cand].get(key), data[ref].get(key)
        d = (a - b) if (a is not None and b is not None) else None
        series.append(None if d is None else round(d, 3))
        if d is None or abs(off) < GAP:
            continue
        (pre if off < 0 else post).append(d)
    if len(pre) < MIN_MONTHS or len(post) < MIN_MONTHS:
        return None, None, series
    return float(np.mean(post) - np.mean(pre)), float(np.mean(pre)), series

# ---------- build pairs ----------
pairs = []
for cand, (tdate, prior) in first_mmts.items():
    if cand not in tmax_a or cand not in meta.index:
        continue
    if not (1982 <= tdate.year <= 2005):
        continue
    t0i = month_index(tdate)
    la, lo = meta.loc[cand, "lat"], meta.loc[cand, "lon"]
    for ref in meta.index:
        if ref == cand or ref not in tmax_a:
            continue
        d_km = havkm(la, lo, meta.loc[ref, "lat"], meta.loc[ref, "lon"])
        if d_km > MAX_KM:
            continue
        # reference must have no documented TEMP equipment change within window
        bad = any(abs(month_index(ev[0]) - t0i) <= WIN + GAP
                  for ev in events.get(ref, []))
        if bad or ref not in events:
            continue
        sx, prex, serx = diff_step(cand, ref, t0i, tmax_a)
        sn, pren, sern = diff_step(cand, ref, t0i, tmin_a)
        if sx is None or sn is None:
            continue
        pairs.append({
            "cand": cand, "ref": ref, "km": round(float(d_km), 1),
            "date": str(tdate)[:10], "prior": prior,
            "step_tmax": round(sx, 3), "step_tmin": round(sn, 3),
            "series_tmax": serx, "series_tmin": sern,
            "cand_name": f"{meta.loc[cand,'name'].strip()}, {meta.loc[cand,'state']}",
            "ref_name": f"{meta.loc[ref,'name'].strip()}, {meta.loc[ref,'state']}",
        })

df = pd.DataFrame([{k: p[k] for k in
                    ("cand", "ref", "km", "date", "step_tmax", "step_tmin")}
                   for p in pairs])
print(f"\npairs: {len(df)} covering {df.cand.nunique()} MMTS stations, "
      f"{df.ref.nunique()} references")

# per-candidate means (avoid multi-ref overweighting)
percand = df.groupby("cand")[["step_tmax", "step_tmin"]].mean()
for v in ["step_tmax", "step_tmin"]:
    m, med, se = percand[v].mean(), percand[v].median(), percand[v].sem()
    print(f"{v}: mean {m:+.3f} C (95% CI +/-{1.96*se:.3f}), median {med:+.3f}")

# ---------- composite epoch series ----------
def composite(key):
    acc = np.zeros(2 * WIN + 1)
    n = np.zeros(2 * WIN + 1)
    for p in pairs:
        ser = p[key]
        pre = [ser[i] for i in range(2 * WIN + 1)
               if ser[i] is not None and i - WIN <= -GAP]
        base = np.mean(pre)
        for i, v in enumerate(ser):
            if v is not None:
                acc[i] += v - base
                n[i] += 1
    return [round(a / c, 4) if c > 20 else None for a, c in zip(acc, n)]

comp = {"tmax": composite("series_tmax"), "tmin": composite("series_tmin")}

# ---------- explorer subset: best pair per candidate, most complete ----------
best = {}
for p in pairs:
    score = sum(v is not None for v in p["series_tmax"]) - p["km"] / 20
    if p["cand"] not in best or score > best[p["cand"]][0]:
        best[p["cand"]] = (score, p)
explorer = sorted((p for _, p in best.values()),
                  key=lambda p: p["step_tmax"])
print(f"explorer pairs: {len(explorer)}")

out = {
    "dataset": DATASET, "win": WIN, "gap": GAP, "max_km": MAX_KM,
    "n_pairs": len(df), "n_candidates": int(df.cand.nunique()),
    "percand_tmax": [round(v, 3) for v in percand.step_tmax],
    "percand_tmin": [round(v, 3) for v in percand.step_tmin],
    "mean_tmax": round(float(percand.step_tmax.mean()), 3),
    "ci_tmax": round(float(1.96 * percand.step_tmax.sem()), 3),
    "mean_tmin": round(float(percand.step_tmin.mean()), 3),
    "ci_tmin": round(float(1.96 * percand.step_tmin.sem()), 3),
    "composite": comp,
    "explorer": explorer,
}
suffix = "" if DATASET == "tob" else f"_{DATASET}"
with open(f"{BASE}/results/mmts_pairs{suffix}.json", "w") as f:
    json.dump(out, f)
print(f"wrote results/mmts_pairs{suffix}.json")
