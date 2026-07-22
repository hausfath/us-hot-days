"""Regional breakdown of hot days (BE) + CONUS TMax/TMin/TAvg trends (NOAA CAG)."""
import glob
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
from scipy import stats

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 150})

# ---------------- load BE counts ------------------------------------------------
files = sorted(glob.glob(f"{BASE}/data/berkeley/counts_*.nc"))
ds = xr.concat([xr.open_dataset(f)[["count", "ndays_valid"]].load() for f in files],
               dim="year")
mask = xr.open_dataset(f"{BASE}/data/conus_mask_1deg.nc").in_conus
land = xr.open_dataset(files[0]).land_mask
cnt95 = ds["count"].sel(threshold="95F").where(ds.ndays_valid >= 355)

# ---------------- map: 1930s minus 2000-2023 ------------------------------------
d30 = cnt95.sel(year=slice(1930, 1939)).mean("year")
drec = cnt95.sel(year=slice(2000, 2023)).mean("year")
diff = (d30 - drec).where(mask > 0)

def state_patches(ax):
    d = json.load(open(f"{BASE}/data/us-states.json"))
    for f in d["features"]:
        if f["properties"]["name"] in {"Alaska", "Hawaii", "Puerto Rico"}:
            continue
        geom = f["geometry"]
        polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        for poly in polys:
            ax.add_patch(PathPatch(MplPath(np.array(poly[0])), facecolor="none",
                                   edgecolor="0.35", lw=0.5))

fig, axes = plt.subplots(2, 1, figsize=(10, 10.5),
                         gridspec_kw={"height_ratios": [1.15, 1]})
ax = axes[0]
pc = ax.pcolormesh(diff.longitude, diff.latitude, diff.values,
                   cmap="RdBu_r", vmin=-25, vmax=25, shading="nearest")
state_patches(ax)
ax.set_xlim(-126, -66); ax.set_ylim(24, 50); ax.set_aspect(1.3)
cb = fig.colorbar(pc, ax=ax, shrink=0.8, pad=0.02)
cb.set_label("Days ≥95°F per year, 1930s minus 2000–2023")
ax.set_title("a) Where the 1930s were hotter: change in days ≥95°F\n"
             "(Berkeley Earth daily TMAX, 1930–1939 average minus 2000–2023 average)",
             loc="left", fontsize=11)

# ---------------- regional series: Dust Bowl core vs rest -----------------------
# Core: southern/central Plains + western Midwest where the 1930s dominate
core = ((ds.latitude >= 30) & (ds.latitude <= 45)).astype(int) * \
       ((ds.longitude >= -104) & (ds.longitude <= -90)).astype(int)
w = np.cos(np.deg2rad(ds.latitude)) * land * mask
valid = ds.ndays_valid.sel(year=1950) >= 0  # placeholder broadcast

def wmean(da, wgt):
    ok = np.isfinite(da)
    return (da * wgt).sum(["latitude", "longitude"]) / wgt.where(ok).sum(["latitude", "longitude"])

core_ts = wmean(cnt95, w * core).to_series()
rest_ts = wmean(cnt95, w * (1 - core)).to_series()
pd.DataFrame({"core": core_ts, "rest": rest_ts}).to_csv(f"{BASE}/results/be_regional_95F.csv")

ax = axes[1]
for s, c, lab in [(core_ts, "#b2182b", "Central US (30–45N, 104–90W)"),
                  (rest_ts, "#2166ac", "Rest of CONUS")]:
    s = s.dropna()
    sm = s.rolling(11, center=True, min_periods=8).mean()
    ax.plot(s.index, s.values, color=c, lw=0.8, alpha=0.35)
    ax.plot(sm.index, sm.values, color=c, lw=2.2, label=lab)
ax.set_xlim(1894, 2026)
ax.set_ylabel("Days ≥95°F per year")
ax.set_title("b) Days ≥95°F, central US vs rest of the country (11-yr means in bold)",
             loc="left", fontsize=11)
ax.legend(frameon=False)
ax.annotate("Data: Berkeley Earth homogenized daily TMAX, 1°×1°, area-weighted. Chart: The Climate Brink",
            xy=(0.0, -0.14), xycoords="axes fraction", fontsize=8, color="0.4")
fig.tight_layout()
fig.savefig(f"{BASE}/figures/fig5_regional.png", bbox_inches="tight")

# stats for the text
for name, s in [("core", core_ts), ("rest", rest_ts)]:
    s = s.dropna()
    d30v = s.loc[1930:1939].mean(); drecv = s.loc[2000:2023].mean()
    print(f"{name}: 1930s={d30v:.2f} 2000-2023={drecv:.2f} ratio={d30v/drecv:.2f}")

# ---------------- CONUS TMax/TMin/TAvg trends (NOAA CAG) ------------------------
fig, ax = plt.subplots(figsize=(10, 5.5))
colors = {"tmax": "#b2182b", "tavg": "0.25", "tmin": "#2166ac"}
labels = {"tmax": "Daily maximum (TMax)", "tavg": "Daily average (TAvg)",
          "tmin": "Daily minimum (TMin)"}
print("\nNOAA CAG CONUS trends:")
for v in ["tmax", "tavg", "tmin"]:
    df = pd.read_csv(f"{BASE}/data/cag_{v}.csv", skiprows=3)
    df["year"] = df.Date // 100
    df = df[df.year <= 2025]
    y = df["Departure from Average"]
    sm = y.rolling(11, center=True, min_periods=8).mean()
    ax.plot(df.year, y, color=colors[v], lw=0.7, alpha=0.3)
    ax.plot(df.year, sm, color=colors[v], lw=2.2, label=labels[v])
    for y0 in [1895, 1970]:
        sub = df[df.year >= y0]
        sl, ic, r, p, se = stats.linregress(sub.year, sub["Departure from Average"])
        print(f"  {v} {y0}-2025: {sl*10:+.2f} F/decade ({sl*10*5/9:+.3f} C/decade) p={p:.1e}")
ax.axhline(0, color="0.7", lw=0.8)
ax.set_ylabel("Anomaly (°F, relative to 1901–2000)")
ax.set_title("Contiguous US annual temperatures, 1895–2025 (11-yr means in bold)",
             fontsize=12)
ax.legend(frameon=False, loc="upper left")
ax.set_xlim(1894, 2026)
ax.annotate("Data: NOAA nClimDiv (Climate at a Glance), annual means. Chart: The Climate Brink",
            xy=(0.0, -0.12), xycoords="axes fraction", fontsize=8, color="0.4")
fig.tight_layout()
fig.savefig(f"{BASE}/figures/fig6_conus_trends.png", bbox_inches="tight")
print("figures written")
