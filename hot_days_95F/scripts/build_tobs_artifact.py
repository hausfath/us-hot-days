"""Inject data JSONs into the TOBs artifact template -> tobs_artifact.html"""
import json

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/hot_days_95F"

tpl = open(f"{BASE}/scripts/tobs_artifact_template.html").read()
matrix = json.dumps(json.load(open(f"{BASE}/results/uscrn_tobs_matrix2.json")),
                    separators=(",", ":"))
episode = json.dumps(json.load(open(f"{BASE}/results/tobs_episode.json")),
                     separators=(",", ":"))
out = tpl.replace("__MATRIX_JSON__", matrix).replace("__EPISODE_JSON__", episode)
with open(f"{BASE}/tobs_artifact.html", "w") as f:
    f.write(out)
print(f"wrote tobs_artifact.html ({len(out)/1024:.0f} KB)")

# standalone copy for GitHub Pages (adds the wrapper the artifact host injects)
import os
os.makedirs(f"{BASE}/../docs", exist_ok=True)
standalone = (
    "<!doctype html>\n<html lang=\"en\">\n"
    "<meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
    "<link rel=\"icon\" href=\"data:image/svg+xml,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<text y='.9em' font-size='90'>🌡️</text></svg>\">\n"
    + out + "\n</html>\n"
)
with open(f"{BASE}/../docs/index.html", "w") as f:
    f.write(standalone)
print("wrote docs/index.html (standalone)")
