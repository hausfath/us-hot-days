# US hot days: raw vs homogenized data

Code and data behind the Climate Brink post **"Hot days and cold biases"**,
which evaluates a viral chart of US days at or above 95°F/100°F/105°F built
from raw GHCN-Daily station data.

## Key results (days ≥95°F per year)

| Series | 1930s | 2000–2023 | ratio |
|---|---|---|---|
| GHCN-Daily raw, 543 long-record stations, gridded | 23.1 | 13.2 | 1.75 |
| Berkeley Earth homogenized, same grid cells | ~8 | ~5.5 | 1.47 |
| Berkeley Earth homogenized, full contiguous US | 7.8 | 7.0 | 1.11 |

The raw and homogenized series track each other closely until ~1980, then
diverge: the divergence coincides with the CRS→MMTS instrument transition and
time-of-observation changes, both of which suppress modern hot day counts in
raw data. Regionally, the 1930s dominance survives only in the Upper Midwest,
Northern Rockies & Plains, and Ohio Valley; the South, Southeast, Southwest,
and West all match or exceed the 1930s today. Globally (on a fixed
century-long-coverage mask), days ≥95°F are up ~73% since the early 20th
century with no 1930s spike at all.

Full methods, caveats, and sensitivity tests: [METHODS.md](METHODS.md).

## Contents

- `scripts/` — the full pipeline, in order:
  1. `download_ghcn.sh` — fetch GHCN-Daily by-station files (~1 GB; also
     requires `ghcnd-inventory.txt`/`ghcnd-stations.txt` from NOAA)
  2. `process_ghcn.py` — per-station annual hot-day counts (QC-filtered)
  3. `aggregate_ghcn.py` — completeness screening, 2°×2° gridding,
     area-weighted CONUS series
  4. `build_conus_mask.py` — 1° CONUS mask from state polygons
  5. `process_be_decade.py` / `process_be_decade_global.py` — Berkeley Earth
     daily TMAX decadal files → per-cell annual exceedance counts (CONUS box /
     global; ~4 GB of downloads, deleted after processing)
  6. `aggregate_be.py`, `aggregate_global.py`, `regional_climate_regions.py`,
     `regional_and_trends.py`, `make_figures.py` — aggregation and figures
- `results/` — derived series (station-year counts, CONUS/regional/global
  annual series). These are sufficient to regenerate every figure without
  re-downloading anything.
- `data/berkeley/counts_*.nc`, `global_counts_*.nc` — per-cell annual
  exceedance counts derived from Berkeley Earth daily TMAX.
- `data/cag_*.csv` — NOAA Climate at a Glance CONUS annual TMax/TMin/TAvg.
- `figures/` — all figures from the post.

## Data sources

- [NOAA GHCN-Daily](https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily)
  (raw daily TMAX; US government work, public domain)
- [Berkeley Earth](https://berkeleyearth.org/data/) gridded daily TMAX
  (CC BY 4.0; Rohde et al)
- [NOAA nClimDiv via Climate at a Glance](https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/)
- US state boundaries GeoJSON from PublicaMundi/MappingAPI

## License

Code is MIT licensed. Derived data products inherit the licenses of their
sources (NOAA: public domain; Berkeley Earth: CC BY 4.0).
