# US hot days: raw vs homogenized data

**Repo layout:** `hot_days_95F/` holds the published blog-post analysis and
interactive demo pipelines (July 2026); `p95_comparison/` holds the follow-on
comparison of CONUS TMax records on a local-95th-percentile basis (in
progress). `docs/` is the GitHub Pages site.

Code and data behind the Climate Brink post **"Hot days and cold biases"**,
which evaluates a viral chart of US days at or above 95°F/100°F/105°F built
from raw GHCN-Daily station data.

**Interactive demos:**

- [Two ways to erase a hot day](https://hausfath.github.io/us-hot-days/)
  replays the historical observation-time (TOBs) and MMTS instrument
  transitions on pristine USCRN hourly data, showing how paperwork alone can
  flip a warming hot-days record (+1.13 days/decade) into an apparently
  cooling one (−0.84 days/decade).
- [The thermometer swap, measured](https://hausfath.github.io/us-hot-days/mmts/)
  measures the MMTS transition bias directly from 385 USHCN stations with
  HOMR-documented installation dates, differenced against unchanged neighbors:
  TMax −0.34 ± 0.06 °C, TMin +0.26 ± 0.08 °C (matching Quayle et al 1991),
  with a composite epoch analysis and a per-station pair explorer.

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

Full methods, caveats, and sensitivity tests: [METHODS.md](hot_days_95F/METHODS.md).

## Contents

- `hot_days_95F/scripts/` — the full pipeline, in order:
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
- `hot_days_95F/results/` — derived series (station-year counts, CONUS/regional/global
  annual series). These are sufficient to regenerate every figure without
  re-downloading anything.
- `hot_days_95F/data/berkeley/counts_*.nc`, `global_counts_*.nc` — per-cell annual
  exceedance counts derived from Berkeley Earth daily TMAX.
- `hot_days_95F/data/cag_*.csv` — NOAA Climate at a Glance CONUS annual TMax/TMin/TAvg.
- `hot_days_95F/figures/` — all figures from the post.

## Interactive demo pipeline

The [hosted demo](https://hausfath.github.io/us-hot-days/) is fully
reproducible from this repo:

1. `hot_days_95F/scripts/process_uscrn_year2.py YEAR` — streams one year of USCRN hourly
   TMAX (CONUS stations) and writes per-station annual counts of days ≥95°F
   under each of 24 simulated observation hours × 5 instrument cold-bias
   levels (0 to −1.0°C) to `hot_days_95F/results/uscrn_tobs_counts2.csv`. Run for
   2005–2025 (~5 GB of downloads total; raw files are not stored).
   (`process_uscrn_year.py` / `uscrn_tobs_counts.csv` are the earlier
   obs-hour-only version, kept for reference.)
2. `hot_days_95F/scripts/aggregate_uscrn_tobs2.py` — screens to a fixed set of 70 stations
   (≥95% complete Apr–Oct hours in ≥20 of 21 years) and builds the
   network-mean matrix `hot_days_95F/results/uscrn_tobs_matrix2.json`
   ([year][obs hour][bias]), plus headline scenario trends.
3. `hot_days_95F/scripts/find_tobs_episode.py STATION YEAR extract` — finds isolated
   double-count episodes (a ≥95°F day preceded and followed by cool days that
   a 5 PM observer books twice) and extracts the 72-hour hourly trace
   (`hot_days_95F/results/tobs_episode.json`). The demo uses Manhattan 6 SSW, KS,
   July 3–5, 2023.
4. `hot_days_95F/scripts/build_tobs_artifact.py` — injects both JSONs into
   `hot_days_95F/scripts/tobs_artifact_template.html`, producing `tobs_artifact.html` and
   the GitHub Pages copy `docs/index.html`.

The derived CSV/JSON files in `hot_days_95F/results/` are committed, so steps 2–4 (and any
re-analysis of the observation-hour × bias matrix) can be run without
re-downloading anything.

The MMTS deep dive has its own pipeline:

1. `hot_days_95F/scripts/fetch_homr_metadata.py` — pulls TEMP equipment histories for all
   1,218 USHCN stations from NOAA HOMR → `hot_days_95F/results/ushcn_equipment.csv`.
2. `hot_days_95F/scripts/analyze_mmts_pairs.py [tob|raw]` — identifies documented
   liquid-in-glass→MMTS transitions (1982–2005), pairs each with USHCN
   neighbors ≤75 km having no documented equipment change within ±4 years,
   and measures the step in the monthly anomaly difference at the documented
   date (USHCN v2.5 monthly, TOB-adjusted by default) →
   `hot_days_95F/results/mmts_pairs.json` (and `_raw` variant).
3. `hot_days_95F/scripts/build_mmts_artifact.py` — builds `mmts_artifact.html` and the
   hosted copy `docs/mmts/index.html`.

USHCN v2.5 monthly tarballs (~20 MB total) download from
`ncei.noaa.gov/pub/data/ushcn/v2.5/`; the derived equipment and pair files are
committed, so steps 2–3 rerun without any downloads.

## Data sources

- [NOAA GHCN-Daily](https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily)
  (raw daily TMAX; US government work, public domain)
- [Berkeley Earth](https://berkeleyearth.org/data/) gridded daily TMAX
  (CC BY 4.0; Rohde et al)
- [NOAA nClimDiv via Climate at a Glance](https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/)
- [NOAA USCRN hourly](https://www.ncei.noaa.gov/pub/data/uscrn/products/hourly02/) (US Climate Reference Network; public domain)
- [NOAA USHCN v2.5 monthly](https://www.ncei.noaa.gov/pub/data/ushcn/v2.5/) and [NOAA HOMR station metadata](https://www.ncei.noaa.gov/access/homr/) (public domain)
- US state boundaries GeoJSON from PublicaMundi/MappingAPI

## License

Code is MIT licensed. Derived data products inherit the licenses of their
sources (NOAA: public domain; Berkeley Earth: CC BY 4.0).
