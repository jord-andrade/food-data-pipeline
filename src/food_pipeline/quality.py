from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

import polars as pl
from pydantic import BaseModel, ConfigDict

from food_pipeline.config import PIPELINE_VERSION, SOURCE_NAME, SOURCE_RELEASE
from food_pipeline.contracts import ALLOWED_UNITS, validate_contract_rows
from food_pipeline.source import SourceTables


class CheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    status: Literal["pass", "fail", "warn"]
    observed: str
    expected: str
    severity: Literal["error", "warning"] = "error"


class QualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pipeline_version: str
    source: str
    source_release: str
    food_rows: int
    nutrient_rows: int
    observation_rows: int
    checks: list[CheckResult]

    @property
    def error_count(self) -> int:
        return sum(check.status == "fail" and check.severity == "error" for check in self.checks)

    @property
    def pass_count(self) -> int:
        return sum(check.status == "pass" for check in self.checks)

    @property
    def warning_count(self) -> int:
        return sum(check.status == "warn" for check in self.checks)


def _check(
    name: str,
    passed: bool,
    observed: object,
    expected: str,
    *,
    severity: Literal["error", "warning"] = "error",
) -> CheckResult:
    return CheckResult(
        name=name,
        status="pass" if passed else ("warn" if severity == "warning" else "fail"),
        observed=str(observed),
        expected=expected,
        severity=severity,
    )


def _orphan_count(frame: pl.DataFrame, key: str, valid_values: Iterable[int]) -> int:
    valid = pl.DataFrame({key: list(valid_values)}, schema={key: pl.Int64})
    return frame.select(key).unique().join(valid, on=key, how="anti").height


def run_quality_checks(tables: SourceTables) -> QualityReport:
    foods = tables.foods
    observations = tables.food_nutrients
    nutrients = tables.nutrients
    categories = tables.categories

    referenced_nutrient_ids = observations.get_column("nutrient_id").unique().to_list()
    referenced_nutrients = nutrients.filter(pl.col("id").is_in(referenced_nutrient_ids))
    validate_contract_rows(
        foods.with_columns(pl.col("publication_date").cast(pl.String)).to_dicts(),
        referenced_nutrients.to_dicts(),
        observations.to_dicts(),
    )

    food_ids = foods.get_column("fdc_id").drop_nulls().to_list()
    nutrient_ids = nutrients.get_column("id").drop_nulls().to_list()
    category_ids = categories.get_column("id").drop_nulls().to_list()
    core_gram_ids = [1003, 1004, 1005, 1063, 1079]
    gram_violations = observations.filter(
        pl.col("nutrient_id").is_in(core_gram_ids) & (pl.col("amount") > 100)
    ).height
    energy_violations = observations.filter(
        (pl.col("nutrient_id") == 1008) & (pl.col("amount") > 1_000)
    ).height
    required_food_nulls = sum(
        foods.select("fdc_id", "description", "publication_date").null_count().row(0)
    )
    observation_nutrient_keys = observations.select(pl.col("nutrient_id").alias("id"))

    checks = [
        _check("food rows present", foods.height > 0, foods.height, "> 0"),
        _check("observation rows present", observations.height > 0, observations.height, "> 0"),
        _check(
            "food primary key unique",
            foods.get_column("fdc_id").n_unique() == foods.height,
            foods.height - foods.get_column("fdc_id").n_unique(),
            "0 duplicates",
        ),
        _check(
            "observation primary key unique",
            observations.get_column("id").n_unique() == observations.height,
            observations.height - observations.get_column("id").n_unique(),
            "0 duplicates",
        ),
        _check(
            "required food values complete",
            required_food_nulls == 0,
            required_food_nulls,
            "0 nulls",
        ),
        _check(
            "descriptions non-blank",
            foods.filter(pl.col("description").str.strip_chars() == "").height == 0,
            foods.filter(pl.col("description").str.strip_chars() == "").height,
            "0 blank values",
        ),
        _check(
            "food foreign keys valid",
            _orphan_count(observations, "fdc_id", food_ids) == 0,
            _orphan_count(observations, "fdc_id", food_ids),
            "0 orphan observations",
        ),
        _check(
            "nutrient foreign keys valid",
            _orphan_count(observation_nutrient_keys, "id", nutrient_ids) == 0,
            _orphan_count(observation_nutrient_keys, "id", nutrient_ids),
            "0 orphan nutrients",
            severity="warning",
        ),
        _check(
            "category foreign keys valid",
            _orphan_count(
                foods.select(pl.col("food_category_id").drop_nulls().alias("id")),
                "id",
                category_ids,
            )
            == 0,
            _orphan_count(
                foods.select(pl.col("food_category_id").drop_nulls().alias("id")),
                "id",
                category_ids,
            ),
            "0 orphan categories",
        ),
        _check(
            "amounts non-negative",
            observations.filter(pl.col("amount") < 0).height == 0,
            observations.filter(pl.col("amount") < 0).height,
            "0 negative values",
            severity="warning",
        ),
        _check(
            "amount completeness disclosed",
            observations.get_column("amount").null_count() == 0,
            observations.get_column("amount").null_count(),
            "0 null amounts",
            severity="warning",
        ),
        _check(
            "nutrient units recognized",
            referenced_nutrients.filter(~pl.col("unit_name").is_in(sorted(ALLOWED_UNITS))).height
            == 0,
            referenced_nutrients.filter(~pl.col("unit_name").is_in(sorted(ALLOWED_UNITS))).height,
            "0 unsupported units",
        ),
        _check(
            "per-100g macro ranges plausible",
            gram_violations == 0,
            gram_violations,
            "0 values above 100 g/100 g",
        ),
        _check(
            "energy range plausible",
            energy_violations == 0,
            energy_violations,
            "0 values above 1,000 kcal/100 g",
        ),
        _check(
            "every food has nutrient evidence",
            observations.get_column("fdc_id").n_unique() == foods.get_column("fdc_id").n_unique(),
            foods.get_column("fdc_id").n_unique() - observations.get_column("fdc_id").n_unique(),
            "0 foods without observations",
        ),
    ]
    return QualityReport(
        pipeline_version=PIPELINE_VERSION,
        source=SOURCE_NAME,
        source_release=SOURCE_RELEASE,
        food_rows=foods.height,
        nutrient_rows=referenced_nutrients.height,
        observation_rows=observations.height,
        checks=checks,
    )
