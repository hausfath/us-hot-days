"""Build a 1x1 degree CONUS mask from US states GeoJSON (excl. AK, HI, PR)."""
import json
import numpy as np
import xarray as xr
from matplotlib.path import Path

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days"

d = json.load(open(f"{BASE}/data/us-states.json"))
EXCLUDE = {"Alaska", "Hawaii", "Puerto Rico"}

paths = []
for f in d["features"]:
    if f["properties"]["name"] in EXCLUDE:
        continue
    geom = f["geometry"]
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for poly in polys:
        # poly[0] is the exterior ring
        paths.append(Path(np.array(poly[0])))

# BE 1-degree grid cell centers over the CONUS box
lats = np.arange(24.5, 50.5, 1.0)
lons = np.arange(-125.5, -65.5, 1.0)
lon2, lat2 = np.meshgrid(lons, lats)
pts = np.column_stack([lon2.ravel(), lat2.ravel()])

inside = np.zeros(len(pts), dtype=bool)
for p in paths:
    inside |= p.contains_points(pts)

mask = inside.reshape(lat2.shape).astype(np.int8)
ds = xr.Dataset(
    {"in_conus": (("latitude", "longitude"), mask)},
    coords={"latitude": lats, "longitude": lons},
)
ds.to_netcdf(f"{BASE}/data/conus_mask_1deg.nc")
print(f"CONUS cells: {mask.sum()} of {mask.size}")
