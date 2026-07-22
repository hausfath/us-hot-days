"""Global land average days >=95F from BE daily TMAX global counts + figure."""
import glob

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 150})

files = sorted(glob.glob(f"{BASE}/data/berkeley/global_counts_*.nc"))
print(f"{len(files)} decade files")
ds = xr.concat([xr.open_dataset(f)[["count", "ndays_valid"]].load() for f in files],
               dim="year")
land = xr.open_dataset(files[0]).land_mask
ds = ds.sel(year=slice(1895, 2023))

complete = ds.ndays_valid >= 355
# fixed spatial mask: only cells with complete data in >=90% of years 1895-2023,
# so changing coverage (38% of land in the 1890s -> ~100% today) cannot fake a trend
fixed = complete.mean("year") >= 0.90
w = np.cos(np.deg2rad(ds.latitude)) * land * fixed
print(f"fixed mask covers {float((np.cos(np.deg2rad(ds.latitude))*land*fixed).sum()/(np.cos(np.deg2rad(ds.latitude))*land).sum()):.0%} of land area")
cnt = ds["count"].where(complete)

num = (cnt * w).sum(["latitude", "longitude"])
den = w.where(complete).sum(["latitude", "longitude"])
glob_ts = (num / den).to_dataset(dim="threshold").to_dataframe().reset_index()
# fraction of land area with complete data (coverage check)
frac = (den.isel(threshold=0) / w.sum()).values if "threshold" in den.dims else (den / w.sum()).values
glob_ts["frac_land_covered"] = frac
glob_ts.to_csv(f"{BASE}/results/be_global_annual.csv", index=False)
print(glob_ts[["year", "95F", "frac_land_covered"]].tail(6).round(2).to_string(index=False))

d = glob_ts.dropna(subset=["95F"])
d = d[d.year >= 1895]
print("\nDecadal means, global land days >=95F:")
d2 = d.copy(); d2["dec"] = d2.year // 10 * 10
print(d2.groupby("dec")[["95F", "frac_land_covered"]].mean().round(2).to_string())

fig, ax = plt.subplots(figsize=(10, 5.5))
ax.bar(d.year, d["95F"], color="#f4a582", width=0.8, label="Days ≥95°F")
ax.bar(d.year, d["100F"], color="#b2182b", width=0.8, label="Days ≥100°F")
ax.bar(d.year, d["105F"], color="#1a1a1a", width=0.8, label="Days ≥105°F")
ax.set_ylabel("Average number of days per year")
ax.set_title("Global land hot days, 1895–2023\n"
             "Berkeley Earth daily TMAX, regions with continuous century-long records",
             fontsize=12)
ax.legend(frameon=False, loc="upper left")
ax.set_xlim(1894, 2026)
ax.annotate("Data: Berkeley Earth gridded daily TMAX (climatology + anomaly), 1°×1°, cos(lat) × land-fraction weighted.\n"
            "Restricted to grid cells with complete data in ≥90% of years 1895–2023 (42% of global land area),\n"
            "so changing station coverage does not affect the trend. Chart: The Climate Brink",
            xy=(0.0, -0.16), xycoords="axes fraction", fontsize=8, color="0.4")
fig.tight_layout()
fig.savefig(f"{BASE}/figures/fig7_global_hotdays.png", bbox_inches="tight")
print("figure written")
