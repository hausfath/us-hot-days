"""Inject data JSONs into the TOBs artifact template -> tobs_artifact.html"""
import json

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days"

tpl = open(f"{BASE}/scripts/tobs_artifact_template.html").read()
matrix = json.dumps(json.load(open(f"{BASE}/results/uscrn_tobs_matrix2.json")),
                    separators=(",", ":"))
episode = json.dumps(json.load(open(f"{BASE}/results/tobs_episode.json")),
                     separators=(",", ":"))
out = tpl.replace("__MATRIX_JSON__", matrix).replace("__EPISODE_JSON__", episode)
with open(f"{BASE}/tobs_artifact.html", "w") as f:
    f.write(out)
print(f"wrote tobs_artifact.html ({len(out)/1024:.0f} KB)")
