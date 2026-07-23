"""Figures for the US hot days analysis."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/hot_days_95F"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 150})

gh = pd.read_csv(f"{BASE}/results/ghcn_conus_annual.csv")
be = pd.read_csv(f"{BASE}/results/be_conus_annual.csv").dropna(subset=["95F"])
bm = pd.read_csv(f"{BASE}/results/be_conus_annual_ghcn_domain.csv").dropna(subset=["95F"])
be = be[be.year >= 1895]
bm = bm[bm.year >= 1895]

def smooth(x, y, n=11):
    s = pd.Series(y.values, index=x.values).rolling(n, center=True, min_periods=8).mean()
    return s.index, s.values

# ---------------- Figure 1: Martz-style, our GHCN gridded version --------------
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.bar(gh.year, gh.n95, color="#f4a582", width=0.8, label="Days ≥95°F")
ax.bar(gh.year, gh.n100, color="#b2182b", width=0.8, label="Days ≥100°F")
ax.bar(gh.year, gh.n105, color="#1a1a1a", width=0.8, label="Days ≥105°F")
ax.set_ylabel("Average number of days per year")
ax.set_title("Conterminous US hot days, 1895–2025\n"
             "543 long-record GHCN-Daily stations, gridded and area-weighted (raw data)",
             fontsize=12)
ax.legend(frameon=False, loc="upper right")
ax.set_xlim(1894, 2026)
ax.annotate("Data: NOAA GHCN-Daily TMAX; long-record stations screened for completeness,\n"
            "averaged on a 2°×2° grid with cos(lat) area weighting. Chart: The Climate Brink",
            xy=(0.0, -0.13), xycoords="axes fraction", fontsize=8, color="0.4")
fig.tight_layout()
fig.savefig(f"{BASE}/figures/fig1_ghcn_hotdays_martz_style.png", bbox_inches="tight")

# ---------------- Figure 2: raw GHCN vs homogenized Berkeley Earth -------------
fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
ax = axes[0]
ax.bar(gh.year, gh.n95, color="#f4a582", width=0.8)
ax.plot(*smooth(gh.year, gh.n95), color="#b2182b", lw=2.2, label="11-yr average")
ax.set_ylabel("Days ≥95°F per year")
ax.set_title("a) Raw station data (GHCN-Daily, 543 long-record stations, gridded)",
             loc="left", fontsize=11)
ax.legend(frameon=False)

ax = axes[1]
ax.bar(be.year, be["95F"], color="#92c5de", width=0.8)
ax.plot(*smooth(be.year, be["95F"]), color="#2166ac", lw=2.2,
        label="11-yr average (full CONUS)")
ax.plot(*smooth(bm.year, bm["95F"]), color="#2166ac", lw=1.6, ls="--",
        label="11-yr average (GHCN station domain only)")
ax.set_ylabel("Days ≥95°F per year")
ax.set_title("b) Homogenized data (Berkeley Earth daily TMAX, 1°×1°, area-weighted)",
             loc="left", fontsize=11)
ax.legend(frameon=False)
ax.set_xlim(1894, 2026)
fig.suptitle("US days at or above 95°F: raw vs homogenized data", y=0.98, fontsize=13)
ax.annotate("Note: gridded fields smooth local extremes, so absolute counts are lower than station-based counts.\n"
            "Berkeley Earth series ends in 2023. Chart: The Climate Brink",
            xy=(0.0, -0.18), xycoords="axes fraction", fontsize=8, color="0.4")
fig.tight_layout()
fig.savefig(f"{BASE}/figures/fig2_raw_vs_homogenized.png", bbox_inches="tight")

# ---------------- Figure 3: normalized comparison, all three series ------------
fig, ax = plt.subplots(figsize=(10, 5.5))
for df, col, c, ls, lab in [
    (gh, "n95", "#b2182b", "-", "GHCN raw stations (gridded)"),
    (bm, "95F", "#2166ac", "--", "Berkeley Earth homogenized (GHCN domain)"),
    (be, "95F", "#2166ac", "-", "Berkeley Earth homogenized (full CONUS)"),
]:
    base = df[(df.year >= 1951) & (df.year <= 1980)][col].mean()
    x, y = smooth(df.year, df[col] / base)
    ax.plot(x, y, color=c, ls=ls, lw=2, label=lab)
ax.axhline(1, color="0.7", lw=0.8)
ax.set_ylabel("Days ≥95°F relative to 1951–1980 average")
ax.set_title("US days ≥95°F, 11-yr means, each series relative to its own 1951–1980 mean",
             fontsize=12)
ax.legend(frameon=False)
ax.set_xlim(1894, 2026)
fig.tight_layout()
fig.savefig(f"{BASE}/figures/fig3_normalized_comparison.png", bbox_inches="tight")

# ---------------- Figure 4: station map ----------------------------------------
meta = pd.read_csv(f"{BASE}/data/ghcn/candidate_stations.csv")
counts = pd.read_csv(f"{BASE}/results/ghcn_station_annual_counts.csv")
counts = counts[(counts.year >= 1895) & (counts.year <= 2025)]
counts["valid"] = counts.warm_days >= 172
nv = counts[counts.valid].groupby("id").year.nunique()
keep = nv[nv >= 0.85 * 131].index
m = meta[meta.id.isin(keep)]
cells = pd.read_csv(f"{BASE}/results/ghcn_cells_used.csv")

fig, ax = plt.subplots(figsize=(10, 6))
import json
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
d = json.load(open(f"{BASE}/data/us-states.json"))
for f in d["features"]:
    if f["properties"]["name"] in {"Alaska", "Hawaii", "Puerto Rico"}:
        continue
    geom = f["geometry"]
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for poly in polys:
        ax.add_patch(PathPatch(MplPath(np.array(poly[0])), facecolor="0.95",
                               edgecolor="0.6", lw=0.4))
for _, r in cells.iterrows():
    ax.add_patch(plt.Rectangle((r.lonbin - 1, r.latbin - 1), 2, 2,
                               facecolor="#f4a582", alpha=0.35, edgecolor="none"))
ax.scatter(m.lon, m.lat, s=12, color="#b2182b", zorder=5, label=f"{len(m)} stations")
ax.set_xlim(-126, -66); ax.set_ylim(24, 50)
ax.set_aspect(1.3)
ax.set_title("Long-record GHCN-Daily TMAX stations, 1895–2025\n"
             "shaded: 2°×2° grid cells used", fontsize=12)
ax.legend(frameon=False, loc="lower left")
fig.tight_layout()
fig.savefig(f"{BASE}/figures/fig4_station_map.png", bbox_inches="tight")
print("figures written")
