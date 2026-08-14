from __future__ import annotations

from pathlib import Path

import duckdb

from food_pipeline.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_builds_parquet_duckdb_manifest_and_public_report(tmp_path: Path) -> None:
    output = tmp_path / "build"
    site = tmp_path / "site"
    result = run_pipeline(ROOT / "data" / "sample", output, site)

    assert result.report.error_count == 0
    assert (output / "manifest.json").is_file()
    assert (output / "parquet" / "food_nutrition_wide.parquet").is_file()
    assert (site / "index.html").is_file()
    assert (site / "quality-report.json").is_file()

    with duckdb.connect(str(output / "food_data.duckdb"), read_only=True) as connection:
        assert connection.execute("SELECT count(*) FROM dim_food").fetchone() == (20,)
        assert connection.execute("SELECT count(*) FROM quarantine_food_nutrient").fetchone() == (
            1,
        )
        top_description = connection.execute(
            "SELECT description FROM food_nutrition_wide "
            "WHERE protein_g IS NOT NULL ORDER BY protein_g DESC LIMIT 1"
        ).fetchone()
        assert top_description is not None


def test_published_report_is_deterministic(tmp_path: Path) -> None:
    first_site = tmp_path / "first-site"
    second_site = tmp_path / "second-site"
    run_pipeline(ROOT / "data" / "sample", tmp_path / "first-build", first_site)
    run_pipeline(ROOT / "data" / "sample", tmp_path / "second-build", second_site)

    assert (first_site / "index.html").read_bytes() == (second_site / "index.html").read_bytes()
    assert (first_site / "quality-report.json").read_bytes() == (
        second_site / "quality-report.json"
    ).read_bytes()
