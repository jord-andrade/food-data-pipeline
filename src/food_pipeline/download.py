from __future__ import annotations

import hashlib
import shutil
import urllib.request
import zipfile
from pathlib import Path

from food_pipeline.config import (
    ARCHIVE_NAME,
    EXTRACTED_DIRECTORY,
    REQUIRED_FILES,
    SOURCE_SHA256,
    SOURCE_URL,
)


class SourceIntegrityError(RuntimeError):
    """Raised when the source archive violates the pinned integrity contract."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_archive(destination: Path, *, force: bool = False) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / ARCHIVE_NAME
    if archive_path.exists() and not force:
        if sha256_file(archive_path) == SOURCE_SHA256:
            return archive_path
        raise SourceIntegrityError(
            f"existing archive checksum differs from pinned release: {archive_path}"
        )

    temporary_path = archive_path.with_suffix(".zip.part")
    request = urllib.request.Request(  # noqa: S310 -- URL is a pinned HTTPS constant.
        SOURCE_URL,
        headers={"User-Agent": "food-data-pipeline/1.0 (+https://github.com/jord-andrade)"},
    )
    with (
        urllib.request.urlopen(request, timeout=120) as response,  # noqa: S310
        temporary_path.open("wb") as destination_file,
    ):
        shutil.copyfileobj(response, destination_file)

    observed = sha256_file(temporary_path)
    if observed != SOURCE_SHA256:
        temporary_path.unlink(missing_ok=True)
        raise SourceIntegrityError(
            f"downloaded archive checksum mismatch: expected {SOURCE_SHA256}, observed {observed}"
        )
    temporary_path.replace(archive_path)
    return archive_path


def extract_archive(archive_path: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    resolved_destination = destination.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            resolved_member = (destination / member.filename).resolve()
            if not resolved_member.is_relative_to(resolved_destination):
                raise SourceIntegrityError(f"unsafe archive member: {member.filename}")
        archive.extractall(destination)

    extracted = destination / EXTRACTED_DIRECTORY
    missing = [name for name in REQUIRED_FILES if not (extracted / name).is_file()]
    if missing:
        raise SourceIntegrityError(
            f"source archive is missing required tables: {', '.join(missing)}"
        )
    return extracted
