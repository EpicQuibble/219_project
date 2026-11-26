"""Refresh the bundled GNIS summit catalog. Run from any working directory."""

import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen
import zipfile

SOURCE = "https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/DomesticNames/DomesticNames_NH_Text.zip"
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "mountains.json"


def main():
    request = Request(SOURCE, headers={"User-Agent": "SummitReady catalog importer/0.1"})
    with urlopen(request, timeout=60) as response:
        archive = response.read()
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        raw = zipped.read("Text/DomesticNames_NH.txt").decode("utf-8-sig")
    mountains = {}
    for row in csv.DictReader(io.StringIO(raw), delimiter="|"):
        if row["feature_class"] != "Summit" or row["state_name"] != "New Hampshire":
            continue
        mountain = {
            "id": row["feature_id"], "name": row["feature_name"],
            "county": row["county_name"], "lat": float(row["prim_lat_dec"]),
            "lon": float(row["prim_long_dec"]),
        }
        if not (42 <= mountain["lat"] <= 46 and -73 <= mountain["lon"] <= -70):
            raise ValueError(f"Unexpected NH summit coordinates: {mountain}")
        mountains[mountain["id"]] = mountain
    if len(mountains) < 1000:
        raise ValueError("Unexpectedly small catalog; refusing to replace the bundled data.")
    result = {
        "source": SOURCE,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "archive_sha256": hashlib.sha256(archive).hexdigest(),
        "coverage": "All GNIS Summit records whose primary state is New Hampshire; includes named hills, excludes unnamed peaks and features classified differently.",
        "mountains": sorted(mountains.values(), key=lambda m: (m["name"].casefold(), m["county"], m["id"])),
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(mountains)} named NH summits to {OUTPUT}")


if __name__ == "__main__":
    main()
