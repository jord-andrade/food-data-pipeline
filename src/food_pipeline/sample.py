from __future__ import annotations

import csv
import json
from pathlib import Path

from food_pipeline.config import REQUIRED_FILES, SOURCE_RELEASE, SOURCE_SHA256, SOURCE_URL

SAMPLE_FDC_IDS = (
    321358,
    321360,
    323294,
    323505,
    325036,
    325430,
    327046,
    328637,
    330137,
    330458,
    331960,
    332282,
    333008,
    333374,
    334194,
    746764,
    746769,
    746771,
    746772,
    746784,
)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def _write(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_sample(source_dir: Path, destination: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (source_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"source is missing required tables: {', '.join(missing)}")

    selected = {str(identifier) for identifier in SAMPLE_FDC_IDS}
    foundation_rows = [
        row for row in _read(source_dir / "foundation_food.csv") if row["fdc_id"] in selected
    ]
    food_rows = [row for row in _read(source_dir / "food.csv") if row["fdc_id"] in selected]
    observation_rows = [
        row for row in _read(source_dir / "food_nutrient.csv") if row["fdc_id"] in selected
    ]
    found = {row["fdc_id"] for row in food_rows}
    if found != selected:
        missing_ids = sorted(selected - found)
        raise ValueError(f"sample food IDs unavailable in pinned release: {missing_ids}")

    nutrient_ids = {row["nutrient_id"] for row in observation_rows}
    nutrient_rows = [row for row in _read(source_dir / "nutrient.csv") if row["id"] in nutrient_ids]
    category_ids = {row["food_category_id"] for row in food_rows if row["food_category_id"]}
    category_rows = [
        row for row in _read(source_dir / "food_category.csv") if row["id"] in category_ids
    ]

    tables = {
        "foundation_food.csv": sorted(foundation_rows, key=lambda row: int(row["fdc_id"])),
        "food.csv": sorted(food_rows, key=lambda row: int(row["fdc_id"])),
        "food_nutrient.csv": sorted(
            observation_rows,
            key=lambda row: (int(row["fdc_id"]), int(row["nutrient_id"]), int(row["id"])),
        ),
        "nutrient.csv": sorted(nutrient_rows, key=lambda row: int(row["id"])),
        "food_category.csv": sorted(category_rows, key=lambda row: int(row["id"])),
    }
    for filename, rows in tables.items():
        source_rows = _read(source_dir / filename)
        _write(destination / filename, rows, list(source_rows[0]))

    provenance = {
        "source": "USDA FoodData Central — Foundation Foods",
        "source_url": SOURCE_URL,
        "source_release": SOURCE_RELEASE,
        "source_sha256": SOURCE_SHA256,
        "license": "CC0 1.0 Universal / U.S. public domain",
        "selection": "20 fixed Foundation Food identifiers covering diverse categories",
        "fdc_ids": list(SAMPLE_FDC_IDS),
    }
    (destination / "SOURCE.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
