from __future__ import annotations

from pathlib import Path

PIPELINE_VERSION = "1.0.0"
SOURCE_NAME = "USDA FoodData Central — Foundation Foods"
SOURCE_RELEASE = "2026-04-30"
SOURCE_URL = (
    "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_csv_2026-04-30.zip"
)
SOURCE_SHA256 = "d6d4f41dcd19a46abcdd67775379cb6f0292ff08daa7e0680fdd0982830bf57b"
ARCHIVE_NAME = "FoodData_Central_foundation_food_csv_2026-04-30.zip"
EXTRACTED_DIRECTORY = "FoodData_Central_foundation_food_csv_2026-04-30"

REQUIRED_FILES = (
    "foundation_food.csv",
    "food.csv",
    "food_nutrient.csv",
    "nutrient.csv",
    "food_category.csv",
)

CORE_NUTRIENTS: dict[int, str] = {
    1008: "energy_kcal",
    1003: "protein_g",
    1004: "fat_g",
    1005: "carbohydrate_g",
    1079: "fiber_g",
    1063: "total_sugars_g",
    1087: "calcium_mg",
    1089: "iron_mg",
    1092: "potassium_mg",
    1093: "sodium_mg",
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]
