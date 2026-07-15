"""One-time, lossless CSV header migration plus frozen-snapshot validation."""

from __future__ import annotations

import csv
import hashlib
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENAMES = {
    "total_parking_spaces": "building_total_parking_spaces",
    "total_floors": "building_floors",
    "total_building_area_sqft": "building_total_area_sqft",
    "elevators": "building_elevators",
}


def migrate(path: Path) -> None:
    with path.open("r", encoding="utf-8", newline="") as source:
        first = source.readline()
        header = next(csv.reader([first]))
        renamed = [RENAMES.get(column, column) for column in header]
        if header == renamed:
            return
        temp = path.with_suffix(path.suffix + ".tmp")
        with temp.open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target, lineterminator="\n")
            writer.writerow(renamed)
            for line in source:
                target.write(line)
        original_mode = path.stat().st_mode
        path.chmod(original_mode | stat.S_IWRITE)
        with temp.open("rb") as source, path.open("wb") as target:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                target.write(chunk)
        temp.unlink()
        path.chmod(original_mode)


def validate(path: Path, active: bool) -> dict[str, object]:
    with path.open("r", encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    ids = [row["property_id"] for row in rows if row.get("property_id")]
    duplicates = len(ids) - len(set(ids)) if active else 0
    invalid_prices = sum(1 for row in rows if row.get("price") and float(row["price"]) < 0)
    invalid_coordinates = sum(1 for row in rows if row.get("latitude") and not (-90 <= float(row["latitude"]) <= 90) or row.get("longitude") and not (-180 <= float(row["longitude"]) <= 180))
    invalid_links = sum(1 for row in rows if row.get("link") and not row["link"].startswith(("http://", "https://")))
    if duplicates or invalid_prices or invalid_coordinates or invalid_links:
        raise ValueError(f"{path.name} failed snapshot validation")
    return {
        "records": len(rows),
        "duplicate_active_ids": duplicates,
        "invalid_prices": invalid_prices,
        "invalid_coordinates": invalid_coordinates,
        "invalid_links": invalid_links,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    for filename in ("active_dld.csv", "historical_dld.csv"):
        csv_path = ROOT / "data" / filename
        migrate(csv_path)
        print(filename, validate(csv_path, active=filename.startswith("active")))
