# Evaluating the Martz US hot days chart

Analysis of CONUS days ≥95°F / ≥100°F / ≥105°F, 1895–2025, built to evaluate the
viral Chris Martz GHCNd chart (`Martz figure.jpeg`). July 2026.

## What Martz's chart appears to do

Average hot-day counts across all reporting GHCNd stations each year. This
confounds network composition with climate: the network grows from a few hundred
stations (1895) to thousands (today), with shifting geography, and uses **raw**
data with known inhomogeneities.

## Our GHCN-Daily version (raw data, controlled network)

- Source: NOAA GHCN-Daily TMAX, by-station files (downloaded 2026-07-21).
- Candidate stations: CONUS, TMAX record spanning ≤1900 to ≥2024 per inventory
  (903 stations downloaded).
- QC: observations with any quality flag dropped. Values are tenths °C;
  thresholds 35.0 / 37.78 / 40.56 °C (95/100/105°F).
- Station-year valid if ≥80% of Apr–Oct days have valid TMAX (≥172 of 214).
- Station kept if valid in ≥85% of years 1895–2025 → **543 stations** (of the
  903 meeting the span requirement).
- Gridded to 2°×2° (station mean within cell), cells present in ≥95% of years
  kept (**130 cells**), cos(lat) area-weighted CONUS mean.
  - Why 130: CONUS spans 233 2°×2° land cells. 66 contain no long-record
    station at all (~75% of those are west of 100°W: Great Basin, Rockies,
    west Texas — few century-long records exist there). Of the 167 with a
    station, 37 fail the ≥95%-of-years continuity screen, mostly cells with
    a single station (55 of 167 cells have exactly one; median is 3) whose
    own gaps leave the cell empty in >5% of years. The fixed-footprint screen
    prevents the effective domain from drifting year to year. Used cells
    cover ~56% of CONUS land, skewed east; the BE domain-matched series is
    the control for this.
- Headline numbers on this base: 1930s = 23.1 days ≥95°F/yr, 2000–2023 = 13.2
  (ratio 1.75); 1936 = 33.1; mean level ≈ 14.4; r = 0.83 with BE on the
  matched domain; BE matched-domain 1930s/recent ratio = 1.47.
- **Sensitivity to completeness screens**: the base screens are moderately
  permissive because volunteer-observed records often have scattered missing
  months (median candidate reports in 126/131 years but a single missing
  summer month can invalidate a year under strict rules). A strict 90%-of-
  Apr–Oct / 90%-of-years variant keeps only 298 stations and 92 cells; other
  variants: 90%/85% → 423 stn, 80%/80% → 625 stn/135 cells. All variants
  correlate at r ≥ 0.986 with the base series. The strict 298-station version
  gives a slightly *higher* 1930s/(2000–2023) ratio (1.93 vs 1.75) because it
  drops proportionally more South/West stations, where recent decades are
  hotter. Conclusions are unchanged under every screen tested.
- Coverage caveat: long-record stations concentrate in the Midwest/East;
  only 116 of 543 are west of 100°W (see fig4_station_map.png).

## Berkeley Earth version (homogenized)

- Source: BE gridded daily TMAX, 1°×1° (Complete_TMAX_Daily_LatLong1_*.nc,
  Nov 2024 vintage; series complete through 2023).
- Absolute TMAX = day-of-year climatology (1951–1980 base) + daily anomaly;
  leap day mapped to day 365.
- Counts per cell-year; cell-years with <355 valid days excluded.
- CONUS mean weighted by cos(lat) × land fraction × CONUS polygon mask
  (819 one-degree cells). Also computed restricted to the 130 GHCN cells
  ("GHCN domain") to separate homogenization effects from coverage effects.

## Key results (days ≥95°F)

| Series                        | 1930s | 2000–2023 | ratio |
|-------------------------------|-------|-----------|-------|
| GHCN raw, long-record gridded | 23.1  | 13.2      | 1.75  |
| BE homogenized, GHCN domain   | ~8    | ~5.5      | 1.47  |
| BE homogenized, full CONUS    | 7.8   | 7.0       | 1.11  |

(GHCN rows reflect the 543-station base; the strict 298-station variant gives
21.1 / 10.9 / 1.93 and BE-matched 1.59.)

- The 1930s Dust Bowl peak is real and survives homogenization — but raw data
  plus the long-record network's Midwest bias roughly double its size relative
  to recent decades.
- Normalized to each series' own 1951–1980 mean (fig3), raw and homogenized
  agree well **until ~1980, then diverge sharply**: raw stays ~1.0× while
  homogenized rises to ~1.4×. This is the signature of the mid-1980s
  CRS→MMTS instrument transition (cooled raw TMax ~0.5°C) and the shift from
  afternoon to morning observation times (TOBs), both of which suppress
  recent hot-day counts in raw data.
- Coverage matters too: full-CONUS BE shows a much smaller 1930s/recent ratio
  than the GHCN-domain BE series because modern extreme heat is concentrated
  in the West/South, which the long-record network undersamples.

## Caveats

- BE absolute-threshold counts are biased at the cell level: the daily
  climatology is spatially smooth, so sharp gradients are smeared (Phoenix
  cell too cool, S. Florida too warm; checked against city normals). Levels
  are therefore not comparable to station counts (spatial smoothing also
  clips extremes — BE CONUS mean ≈ 5 days vs GHCN stations ≈ 12); trends and
  interannual variability are robust (r=0.83 with GHCN on matched domain).
- 2021 discrepancy checked: BE and GHCN both below average; BE lower because
  2021's heat was concentrated in the cool PNW where +1°C rarely crosses 95°F.
- GHCN series is raw by design (to mirror Martz); it inherits TOBs and
  instrument biases. That is the point of the comparison.

## Additions (post-draft)

- **Regional breakdown** (`scripts/regional_and_trends.py`, fig5): 1930s minus
  2000–2023 days ≥95°F map; central US (30–45N, 104–90W) 1930s=15.5 vs
  recent=11.1 (1.39×); rest of CONUS 4.9 vs 5.5 (0.90× — recent is higher).
- **Nine NOAA climate regions** (`scripts/regional_climate_regions.py`,
  fig5_regions_3x3, `results/be_region_95F.csv`): state-based region masks on
  the 1° grid (cell centers point-in-polygon). 1930s/2000–2023 ratios:
  Upper Midwest 15.3, N. Rockies & Plains 8.7, Ohio Valley 4.1 (all peak 1936);
  South 0.99 (peak 2011), Southeast 0.75, Southwest 0.79, West 0.78 (W/SW peak
  2020), Northeast 1.52 (tiny base, <1 day/yr), Northwest 0.46 (<0.1 day/yr).
  This figure replaced the map+central-vs-rest version as Figure 4 in the draft.
- **CONUS TMax/TMin/TAvg trends** (fig6): NOAA nClimDiv via Climate at a Glance
  (`data/cag_*.csv`). 1970–2025 trends ≈ +0.51 to +0.52 F/decade for all three.
- **Global land hot days** (`scripts/process_be_decade_global.py`,
  `aggregate_global.py`, fig7_global_hotdays): BE files re-downloaded and
  deleted again after extracting global per-cell counts
  (`data/berkeley/global_counts_*.nc`). Figure reproduces the Martz/Figure-1
  design (overlaid 95/100/105°F bars) with global data.
  IMPORTANT: computed on a fixed mask of cells complete in ≥90% of years
  1895–2023 (42% of land, NH-heavy) because naive coverage-following averaging
  triples the series (12→37 days) as hot regions enter the record. Fixed-mask
  results, 1895–1924 vs 2014–2023: ≥95°F 12.8→22.1 (+73%), ≥100°F 3.0→7.5
  (2.5×), ≥105°F 0.32→1.57 (4.9×); all top-10 ≥95°F years since 1998;
  1936 = 15.1 days.

## Files

- `scripts/` — full pipeline: download → process → aggregate → figures.
- `results/ghcn_station_annual_counts.csv` — per-station annual counts (raw
  station files deleted after processing; this is sufficient to redo aggregation).
- `results/ghcn_conus_annual.csv`, `be_conus_annual.csv`,
  `be_conus_annual_ghcn_domain.csv` — final CONUS series.
- `data/berkeley/counts_*.nc` — per-cell BE annual counts (raw netCDFs deleted).
- `figures/fig1–fig4` — Martz-style chart, raw-vs-homogenized panels,
  normalized comparison, station map.
