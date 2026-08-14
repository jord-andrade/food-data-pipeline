from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from food_pipeline.config import REQUIRED_FILES


class SourceContractError(RuntimeError):
    """Raised when required source tables or columns are unavailable."""


@dataclass(frozen=True)
class SourceTables:
    foods: pl.DataFrame
    food_nutrients: pl.DataFrame
    nutrients: pl.DataFrame
    categories: pl.DataFrame


TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "foundation_food.csv": ("fdc_id",),
    "food.csv": ("fdc_id", "data_type", "description", "food_category_id", "publication_date"),
    "food_nutrient.csv": ("id", "fdc_id", "nutrient_id", "amount", "data_points"),
    "nutrient.csv": ("id", "name", "unit_name", "nutrient_nbr", "rank"),
    "food_category.csv": ("id", "code", "description"),
}


def _ensure_source_files(source_dir: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (source_dir / name).is_file()]
    if missing:
        raise SourceContractError(f"missing source tables: {', '.join(missing)}")


def _read_csv(path: Path, columns: tuple[str, ...], schema: dict[str, Any]) -> pl.DataFrame:
    try:
        return pl.read_csv(
            path,
            columns=list(columns),
            schema_overrides=schema,
            null_values=[""],
            encoding="utf8-lossy",
            infer_schema_length=10_000,
        )
    except (pl.exceptions.ColumnNotFoundError, pl.exceptions.SchemaError) as error:
        raise SourceContractError(f"invalid schema in {path.name}: {error}") from error


def load_source(source_dir: Path) -> SourceTables:
    source_dir = source_dir.resolve()
    _ensure_source_files(source_dir)

    foundation_ids = _read_csv(
        source_dir / "foundation_food.csv",
        TABLE_COLUMNS["foundation_food.csv"],
        {"fdc_id": pl.Int64},
    ).unique()
    foods = _read_csv(
        source_dir / "food.csv",
        TABLE_COLUMNS["food.csv"],
        {
            "fdc_id": pl.Int64,
            "data_type": pl.String,
            "description": pl.String,
            "food_category_id": pl.Int64,
            "publication_date": pl.String,
        },
    ).join(foundation_ids, on="fdc_id", how="inner")
    foods = foods.with_columns(pl.col("publication_date").str.to_date("%Y-%m-%d", strict=True))

    food_nutrients = _read_csv(
        source_dir / "food_nutrient.csv",
        TABLE_COLUMNS["food_nutrient.csv"],
        {
            "id": pl.Int64,
            "fdc_id": pl.Int64,
            "nutrient_id": pl.Int64,
            "amount": pl.Float64,
            "data_points": pl.Int64,
        },
    ).join(foundation_ids, on="fdc_id", how="inner")
    nutrients = _read_csv(
        source_dir / "nutrient.csv",
        TABLE_COLUMNS["nutrient.csv"],
        {
            "id": pl.Int64,
            "name": pl.String,
            "unit_name": pl.String,
            "nutrient_nbr": pl.String,
            "rank": pl.Float64,
        },
    )
    categories = _read_csv(
        source_dir / "food_category.csv",
        TABLE_COLUMNS["food_category.csv"],
        {"id": pl.Int64, "code": pl.String, "description": pl.String},
    )

    return SourceTables(
        foods=foods.sort("fdc_id"),
        food_nutrients=food_nutrients.sort(["fdc_id", "nutrient_id", "id"]),
        nutrients=nutrients.sort("id"),
        categories=categories.sort("id"),
    )
