from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from food_pipeline.quality import QualityReport, run_quality_checks
from food_pipeline.report import render_quality_site, write_quality_json
from food_pipeline.source import load_source
from food_pipeline.transform import create_analytics, write_analytics


class DataQualityError(RuntimeError):
    """Raised when a blocking quality contract fails."""


@dataclass(frozen=True)
class PipelineResult:
    report: QualityReport
    output_dir: Path
    site_dir: Path


def run_pipeline(source_dir: Path, output_dir: Path, site_dir: Path) -> PipelineResult:
    tables = load_source(source_dir)
    report = run_quality_checks(tables)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_quality_json(report, output_dir / "quality-report.json")
    if report.error_count:
        raise DataQualityError(f"{report.error_count} blocking data quality checks failed")

    outputs = create_analytics(tables)
    write_analytics(outputs, output_dir)
    render_quality_site(report, outputs, site_dir)
    return PipelineResult(report=report, output_dir=output_dir, site_dir=site_dir)
