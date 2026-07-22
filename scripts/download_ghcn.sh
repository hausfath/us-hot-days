#!/bin/bash
cd "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/data/ghcn/stations"
xargs -P 8 -I {} curl -s -f -o "{}.csv.gz" "https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/{}.csv.gz" < ../station_ids.txt
echo "DONE. Files: $(ls *.csv.gz 2>/dev/null | wc -l)"
