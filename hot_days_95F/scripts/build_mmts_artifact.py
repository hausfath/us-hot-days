"""Inject MMTS pair data into template -> mmts_artifact.html + docs/mmts/index.html"""
import json
import os

BASE = "/Users/hausfath/Desktop/Climate Science/The Climate Brink/US hot days/hot_days_95F"

d = json.load(open(f"{BASE}/results/mmts_pairs.json"))
tpl = open(f"{BASE}/scripts/mmts_artifact_template.html").read()
tpl = (tpl.replace("__MEAN_TMAX__", f"{d['mean_tmax']:.2f}".replace("-", "&minus;"))
          .replace("__CI_TMAX__", f"{d['ci_tmax']:.2f}")
          .replace("__MEAN_TMIN__", f"{d['mean_tmin']:.2f}")
          .replace("__CI_TMIN__", f"{d['ci_tmin']:.2f}"))
out = tpl.replace("__MMTS_JSON__", json.dumps(d, separators=(",", ":")))
with open(f"{BASE}/mmts_artifact.html", "w") as f:
    f.write(out)
print(f"wrote mmts_artifact.html ({len(out)/1024:.0f} KB)")

os.makedirs(f"{BASE}/../docs/mmts", exist_ok=True)
standalone = (
    "<!doctype html>\n<html lang=\"en\">\n"
    "<meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
    "<link rel=\"icon\" href=\"data:image/svg+xml,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<text y='.9em' font-size='90'>📏</text></svg>\">\n"
    + out + "\n</html>\n"
)
with open(f"{BASE}/../docs/mmts/index.html", "w") as f:
    f.write(standalone)
print("wrote docs/mmts/index.html")
