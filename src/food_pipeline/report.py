from __future__ import annotations

import html
import json
from pathlib import Path

import polars as pl

from food_pipeline.config import CORE_NUTRIENTS, SOURCE_RELEASE, SOURCE_URL
from food_pipeline.quality import QualityReport
from food_pipeline.transform import AnalyticsOutputs


def _format_amount(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, (int, float)):
        return f"{value:,.1f}"
    return html.escape(str(value))


def _completeness(outputs: AnalyticsOutputs) -> list[tuple[str, int, float]]:
    frame = outputs.food_nutrition_wide
    values: list[tuple[str, int, float]] = []
    for column in CORE_NUTRIENTS.values():
        present = frame.select(pl.col(column).is_not_null().sum()).item()
        percentage = round((present / frame.height) * 100, 1) if frame.height else 0
        values.append((column, present, percentage))
    return values


def _top_protein(outputs: AnalyticsOutputs) -> list[dict[str, object]]:
    return (
        outputs.food_nutrition_wide.filter(pl.col("protein_g").is_not_null())
        .sort("protein_g", descending=True)
        .select("fdc_id", "description", "category", "protein_g", "energy_kcal", "fiber_g")
        .head(6)
        .to_dicts()
    )


def render_quality_site(
    report: QualityReport, outputs: AnalyticsOutputs, destination: Path
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    check_rows = "".join(
        (
            f'<tr><td><span class="status {check.status}">{check.status}</span></td>'
            f"<th>{html.escape(check.name)}</th><td>{html.escape(check.observed)}</td>"
            f"<td>{html.escape(check.expected)}</td></tr>"
        )
        for check in report.checks
    )
    completeness_cards = "".join(
        (
            '<article class="coverage-card">'
            f"<div><strong>{html.escape(column.replace('_', ' '))}</strong><span>{present}/{report.food_rows}</span></div>"
            f'<div class="bar"><i style="width:{percentage}%"></i></div><p>{percentage}% complete</p></article>'
        )
        for column, present, percentage in _completeness(outputs)
    )
    food_rows = "".join(
        (
            f'<tr><td class="mono">{row["fdc_id"]}</td><th>{html.escape(str(row["description"]))}</th>'
            f"<td>{html.escape(str(row['category']))}</td><td>{_format_amount(row['protein_g'])} g</td>"
            f"<td>{_format_amount(row['energy_kcal'])} kcal</td><td>{_format_amount(row['fiber_g'])} g</td></tr>"
        )
        for row in _top_protein(outputs)
    )
    blocking_checks = [check for check in report.checks if check.severity == "error"]
    blocking_passes = sum(check.status == "pass" for check in blocking_checks)
    score = round((blocking_passes / len(blocking_checks)) * 100)
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NutriTrace · USDA data quality report</title>
  <meta name="description" content="Reproducible quality evidence for a CC0 USDA FoodData Central Foundation Foods pipeline.">
  <meta property="og:title" content="NutriTrace · Data should arrive with receipts">
  <meta property="og:description" content="Contracts, lineage, Parquet and DuckDB over USDA Foundation Foods.">
  <meta property="og:type" content="website">
  <meta property="og:image" content="https://nutritrace-data.vercel.app/og-card.svg">
  <link rel="canonical" href="https://nutritrace-data.vercel.app/">
  <link rel="icon" href="/icon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="#top"><span class="brand-mark">N</span>NutriTrace</a>
    <nav aria-label="Primary"><a href="#quality">Quality</a><a href="#lineage">Lineage</a><a href="#query">Query</a><a class="source-link" href="https://github.com/jord-andrade/food-data-pipeline">Source ↗</a></nav>
  </header>
  <main id="top">
    <section class="hero">
      <div class="hero-copy"><p class="eyebrow">USDA FOODDATA CENTRAL / FOUNDATION FOODS</p><h1>A public dataset should arrive <em>with receipts.</em></h1><p class="lede">A reproducible pipeline that pins the source, enforces contracts, builds analytical tables, and publishes the evidence.</p><div class="hero-actions"><a class="button primary" href="#quality">Inspect quality</a><a class="button" href="{html.escape(SOURCE_URL)}">Official release ↗</a></div></div>
      <aside class="score-card" aria-label="Quality score {score} percent"><span class="ring" style="--score:{score * 3.6}deg"><strong>{score}</strong><small>/ 100</small></span><p>All {blocking_passes} blocking checks passed. {report.warning_count} source warnings are visible and quarantined.</p><dl><div><dt>Release</dt><dd>{SOURCE_RELEASE}</dd></div><div><dt>License</dt><dd>CC0 1.0</dd></div></dl></aside>
    </section>

    <section class="stat-strip" aria-label="Pipeline summary"><article><span>01</span><strong>{report.food_rows}</strong><p>Foundation foods</p></article><article><span>02</span><strong>{report.observation_rows:,}</strong><p>Nutrient observations</p></article><article><span>03</span><strong>{report.nutrient_rows}</strong><p>Referenced nutrients</p></article><article><span>04</span><strong>5</strong><p>Published Parquet layers</p></article></section>

    <section class="section" id="quality"><div class="section-heading"><div><p class="eyebrow">QUALITY CONTRACT</p><h2>Nothing passes silently.</h2></div><p>Primary keys, foreign keys, nulls, units, ranges, and evidence coverage are tested before an analytical artifact is trusted.</p></div><div class="table-wrap"><table><caption class="sr-only">Data quality checks</caption><thead><tr><th>Status</th><th>Contract</th><th>Observed</th><th>Expected</th></tr></thead><tbody>{check_rows}</tbody></table></div></section>

    <section class="section coverage"><div class="section-heading"><div><p class="eyebrow">CORE NUTRIENT COVERAGE</p><h2>Missingness is visible.</h2></div><p>Completeness is reported, never imputed. A blank analytical value remains an explicit absence.</p></div><div class="coverage-grid">{completeness_cards}</div></section>

    <section class="section lineage" id="lineage"><div class="section-heading"><div><p class="eyebrow">DATA LINEAGE</p><h2>One source. Four useful layers.</h2></div></div><ol><li><span>01</span><div><strong>Acquire</strong><p>Pinned USDA archive + SHA-256 verification</p></div></li><li><span>02</span><div><strong>Validate</strong><p>Typed schemas + relational quality gates</p></div></li><li><span>03</span><div><strong>Transform</strong><p>Dimensions, long fact, and wide nutrition profile</p></div></li><li><span>04</span><div><strong>Serve</strong><p>Compressed Parquet + indexed DuckDB + this report</p></div></li></ol></section>

    <section class="section" id="query"><div class="section-heading"><div><p class="eyebrow">QUERYABLE EVIDENCE</p><h2>From raw tables to an answer.</h2></div><p>The wide table stays convenient for analysis while the long fact preserves nutrient-level lineage.</p></div><div class="query-grid"><pre><code>SELECT
  description,
  category,
  protein_g,
  energy_kcal,
  fiber_g
FROM food_nutrition_wide
WHERE protein_g IS NOT NULL
ORDER BY protein_g DESC
LIMIT 6;</code></pre><div class="table-wrap compact"><table><caption class="sr-only">Foods with the highest protein in the committed sample</caption><thead><tr><th>FDC ID</th><th>Food</th><th>Category</th><th>Protein</th><th>Energy</th><th>Fiber</th></tr></thead><tbody>{food_rows}</tbody></table></div></div></section>

    <section class="cta"><p class="eyebrow">REPRODUCE IT</p><h2>Clone. Run one command.<br>Get the same validated layer.</h2><pre><code>uv sync --frozen
uv run food-pipeline run</code></pre><a class="button primary" href="https://github.com/jord-andrade/food-data-pipeline">Open repository ↗</a></section>
  </main>
  <footer><span>NutriTrace / public engineering case study</span><span>USDA FoodData Central · CC0 1.0 · Built by <a href="https://jord-andrade.dev">Jordan Andrade</a></span></footer>
</body>
</html>
"""
    (destination / "index.html").write_text(document, encoding="utf-8", newline="\n")
    (destination / "quality-report.json").write_text(
        report.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_quality_json(report: QualityReport, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report.model_dump(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
