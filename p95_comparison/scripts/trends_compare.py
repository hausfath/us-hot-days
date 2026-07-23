"""Compare four CONUS TMax records on the local-p95 basis: trends + figure.

Series: GHCN raw (530 USHCN stations), GHCN homogenized (same stations,
USHCN monthly breakpoint adjustments applied to daily), Berkeley Earth
(1x1 gridded), ERA5 (0.25 gridded, 1960+).
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/p95_comparison"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 150})

stn = pd.read_csv(f"{BASE}/results/conus_p95_stations_adw.csv").set_index("year")
stn22 = pd.read_csv(f"{BASE}/results/conus_p95_stations.csv").set_index("year")
be = pd.read_csv(f"{BASE}/results/be_tx95p_annual.csv").set_index("year")["CONUS"]
try:
    era = pd.read_csv(f"{BASE}/results/conus_p95_era5.csv").set_index("year")["era5"]
except FileNotFoundError:
    era = pd.Series(dtype=float)
    print("NOTE: ERA5 series not available yet")

series = {
    "GHCN raw stations": stn.ghcn_raw_adw,
    "GHCN homogenized (USHCN breakpoints)": stn.ghcn_homog_adw,
    "Berkeley Earth": be.dropna(),
    "ERA5": era.dropna(),
}
COLS = {"GHCN raw stations": "#b2182b",
        "GHCN homogenized (USHCN breakpoints)": "#e08214",
        "Berkeley Earth": "#2166ac",
        "ERA5": "#35978f"}

def trend(s, y0):
    s = s.loc[y0:]
    if len(s) < 20:
        return None
    r = stats.linregress(s.index, s.values)
    return r.slope * 10, 1.96 * r.stderr * 10

rows = []
print(f"{'series':38s} {'1895-':>16s} {'1930-':>16s} {'1960-':>16s}")
for name, s in series.items():
    cells = []
    row = {"series": name}
    for y0 in [1895, 1930, 1960]:
        t = trend(s, y0)
        if t is None:
            cells.append(f"{'—':>16s}")
            row[f"trend_{y0}"] = None
        else:
            cells.append(f"{t[0]:+.2f}±{t[1]:.2f}".rjust(16))
            row[f"trend_{y0}"] = round(t[0], 3)
            row[f"ci_{y0}"] = round(t[1], 3)
    rows.append(row)
    print(f"{name:38s} {''.join(cells)}")
pd.DataFrame(rows).to_csv(f"{BASE}/results/p95_trends.csv", index=False)

# ---------------- figure ----------------
fig, axes = plt.subplots(2, 1, figsize=(10, 9),
                         gridspec_kw={"height_ratios": [1.4, 1]})
ax = axes[0]
for name, s in series.items():
    if len(s) == 0:
        continue
    sm = s.rolling(11, center=True, min_periods=8).mean()
    ax.plot(s.index, s.values, color=COLS[name], lw=0.6, alpha=0.25)
    ax.plot(sm.index, sm.values, color=COLS[name], lw=2.2, label=name)
ax.axhline(18.26, color="0.6", lw=0.8, ls=":")
ax.set_ylabel("Days > local 95th percentile")
ax.set_title("CONUS days above the local 95th percentile of daily TMax\n"
             "(per-station/per-cell thresholds, 1961–1990 base; stations gridded by ADW,\n"
             "full CONUS coverage; 11-yr means in bold)", fontsize=12)
ax.legend(frameon=False, fontsize=9)
ax.set_xlim(1894, 2026)

ax = axes[1]
xpos = np.arange(3)
width = 0.2
for k, (name, s) in enumerate(series.items()):
    vals, errs, xs = [], [], []
    for j, y0 in enumerate([1895, 1930, 1960]):
        t = trend(s, y0)
        if t is None:
            continue
        vals.append(t[0]); errs.append(t[1]); xs.append(j + (k - 1.5) * width)
    ax.bar(xs, vals, width * 0.9, yerr=errs, color=COLS[name], capsize=3,
           error_kw={"lw": 1})
ax.axhline(0, color="0.5", lw=0.8)
ax.set_xticks(xpos)
ax.set_xticklabels(["since 1895", "since 1930", "since 1960"])
ax.set_ylabel("Trend (days/decade)")
ax.set_title("Linear trends with 95% CI", fontsize=11, loc="left")
fig.tight_layout()
fig.savefig(f"{BASE}/figures/p95_comparison.png", bbox_inches="tight")
print("\nfigure written")
