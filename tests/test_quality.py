from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import polars as pl

from food_pipeline.quality import run_quality_checks
from food_pipeline.source import load_source

ROOT = Path(__file__).resolve().parents[1]


def test_committed_sample_passes_blocking_contracts_and_discloses_source_warnings() -> None:
    report = run_quality_checks(load_source(ROOT / "data" / "sample"))

    assert report.error_count == 0
    assert report.warning_count == 2
    assert {check.name for check in report.checks if check.status == "warn"} == {
        "amount completeness disclosed",
        "nutrient foreign keys valid",
    }


def test_duplicate_food_key_is_a_blocking_failure() -> None:
    tables = load_source(ROOT / "data" / "sample")
    duplicated_foods = pl.concat([tables.foods, tables.foods.head(1)])
    report = run_quality_checks(replace(tables, foods=duplicated_foods))

    assert report.error_count == 1
    duplicate_check = next(
        check for check in report.checks if check.name == "food primary key unique"
    )
    assert duplicate_check.status == "fail"
