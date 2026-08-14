from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from food_pipeline.config import SOURCE_SHA256, SOURCE_URL
from food_pipeline.download import SourceIntegrityError, extract_archive, sha256_file


def test_source_is_pinned_to_https_and_sha256() -> None:
    assert SOURCE_URL == (
        "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_csv_2026-04-30.zip"
    )
    assert len(SOURCE_SHA256) == 64
    int(SOURCE_SHA256, 16)


def test_sha256_file_is_reproducible(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.txt"
    fixture.write_bytes(b"FoodData Central\n")
    assert (
        sha256_file(fixture) == "cda04d921f21b5794fa4c1883599c8e28e7913467233424c3dec043c2c7a8cdb"
    )


def test_extraction_rejects_path_traversal(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "unsafe")

    with pytest.raises(SourceIntegrityError, match="unsafe archive member"):
        extract_archive(archive_path, tmp_path / "extract")
