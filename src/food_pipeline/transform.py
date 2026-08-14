from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import duckdb
import polars as pl

from food_pipeline.config import CORE_NUTRIENTS, PIPELINE_VERSION, SOURCE_RELEASE
from food_pipeline.source import SourceTables


@dataclass(frozen=True)
class AnalyticsOutputs:
    dim_food: pl.DataFrame
    dim_nutrient: pl.DataFrame
    fact_food_nutrient: pl.DataFrame
    food_nutrition_wide: pl.DataFrame
    quarantine_food_nutrient: pl.DataFrame


def create_analytics(tables: SourceTables) -> AnalyticsOutputs:
    category_lookup = tables.categories.select(
        pl.col("id").alias("food_category_id"),
        pl.col("code").alias("category_code"),
        pl.col("description").alias("category"),
    )
    dim_food = (
        tables.foods.join(category_lookup, on="food_category_id", how="left")
        .select(
            "fdc_id",
            "description",
            "category_code",
            "category",
            "publication_date",
        )
        .sort("fdc_id")
    )
    referenced_ids = tables.food_nutrients.get_column("nutrient_id").drop_nulls().unique().to_list()
    dim_nutrient = (
        tables.nutrients.filter(pl.col("id").is_in(referenced_ids))
        .rename({"id": "nutrient_id"})
        .sort("nutrient_id")
    )
    valid_nutrient_ids = dim_nutrient.get_column("nutrient_id").to_list()
    valid_observations = tables.food_nutrients.filter(
        pl.col("nutrient_id").is_in(valid_nutrient_ids)
        & pl.col("amount").is_not_null()
        & (pl.col("amount") >= 0)
    )
    quarantine = tables.food_nutrients.filter(
        ~pl.col("nutrient_id").is_in(valid_nutrient_ids)
        | pl.col("amount").is_null()
        | (pl.col("amount") < 0)
    ).with_columns(
        pl.when(pl.col("amount").is_null())
        .then(pl.lit("missing_amount"))
        .when(pl.col("amount") < 0)
        .then(pl.lit("negative_amount"))
        .otherwise(pl.lit("missing_nutrient_dimension"))
        .alias("rejection_reason")
    )
    fact = (
        valid_observations.join(
            dim_nutrient.select("nutrient_id", "name", "unit_name"),
            on="nutrient_id",
            how="left",
        )
        .select(
            pl.col("id").alias("food_nutrient_id"),
            "fdc_id",
            "nutrient_id",
            pl.col("name").alias("nutrient"),
            pl.col("unit_name").alias("unit"),
            "amount",
            "data_points",
        )
        .sort(["fdc_id", "nutrient_id", "food_nutrient_id"])
    )

    wide = dim_food.clone()
    for nutrient_id, column_name in CORE_NUTRIENTS.items():
        measure = (
            tables.food_nutrients.filter(pl.col("nutrient_id") == nutrient_id)
            .group_by("fdc_id")
            .agg(pl.col("amount").mean().round(4).alias(column_name))
        )
        wide = wide.join(measure, on="fdc_id", how="left")

    return AnalyticsOutputs(
        dim_food=dim_food,
        dim_nutrient=dim_nutrient,
        fact_food_nutrient=fact,
        food_nutrition_wide=wide.sort("fdc_id"),
        quarantine_food_nutrient=quarantine.sort(["fdc_id", "nutrient_id", "id"]),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_analytics(outputs: AnalyticsOutputs, output_dir: Path) -> dict[str, str]:
    parquet_dir = output_dir / "parquet"
    parquet_dir.mkdir(parents=True, exist_ok=True)
    frames = {
        "dim_food": outputs.dim_food,
        "dim_nutrient": outputs.dim_nutrient,
        "fact_food_nutrient": outputs.fact_food_nutrient,
        "food_nutrition_wide": outputs.food_nutrition_wide,
        "quarantine_food_nutrient": outputs.quarantine_food_nutrient,
    }
    files: dict[str, Path] = {}
    for name, frame in frames.items():
        path = parquet_dir / f"{name}.parquet"
        frame.write_parquet(path, compression="zstd", statistics=True)
        files[name] = path

    database_path = output_dir / "food_data.duckdb"
    database_path.unlink(missing_ok=True)
    with duckdb.connect(str(database_path)) as connection:
        for name, path in files.items():
            connection.execute(
                f"CREATE TABLE {name} AS SELECT * FROM read_parquet(?)",  # noqa: S608
                [str(path)],
            )
        connection.execute("CREATE INDEX idx_fact_food ON fact_food_nutrient(fdc_id)")
        connection.execute("CREATE INDEX idx_fact_nutrient ON fact_food_nutrient(nutrient_id)")

    artifacts = {
        path.relative_to(output_dir).as_posix(): _sha256(path)
        for path in [*files.values(), database_path]
    }
    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "source_release": SOURCE_RELEASE,
        "artifacts": artifacts,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return artifacts
