from __future__ import annotations

import argparse
from pathlib import Path

from food_pipeline.config import project_root
from food_pipeline.download import download_archive, extract_archive
from food_pipeline.pipeline import run_pipeline
from food_pipeline.sample import build_sample


def _parser() -> argparse.ArgumentParser:
    root = project_root()
    parser = argparse.ArgumentParser(
        prog="food-pipeline",
        description="Build a validated analytical layer from USDA Foundation Foods.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="validate, transform, and publish a source directory")
    run.add_argument("--source", type=Path, default=root / "data" / "sample")
    run.add_argument("--output", type=Path, default=root / "build")
    run.add_argument("--site", type=Path, default=root / "site")

    download = subparsers.add_parser("download", help="download and verify the pinned USDA release")
    download.add_argument("--destination", type=Path, default=root / "data" / "raw")
    download.add_argument("--force", action="store_true")

    sample = subparsers.add_parser("build-sample", help="rebuild the committed 20-food sample")
    sample.add_argument("--source", type=Path, required=True)
    sample.add_argument("--destination", type=Path, default=root / "data" / "sample")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "download":
        archive = download_archive(args.destination, force=args.force)
        extracted = extract_archive(archive, args.destination)
        print(f"verified source extracted to {extracted}")
        return
    if args.command == "build-sample":
        build_sample(args.source, args.destination)
        print(f"sample written to {args.destination}")
        return

    result = run_pipeline(args.source, args.output, args.site)
    print(
        f"pipeline passed {result.report.pass_count} checks with "
        f"{result.report.warning_count} source warnings and no blocking failures; "
        f"wrote {result.report.observation_rows:,} observations to {result.output_dir}"
    )
