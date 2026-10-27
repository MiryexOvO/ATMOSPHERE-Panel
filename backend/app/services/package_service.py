from __future__ import annotations
from pathlib import Path
from .archive_service import extract_archive, find_core_candidates

class PackageService:
    """Application service for safe archive extraction and core discovery."""
    def inspect(self, archive: Path, workspace: Path) -> list[dict]:
        extract_archive(archive, workspace)
        return find_core_candidates(workspace)

    def extract(self, archive: Path, destination: Path) -> list[dict]:
        extract_archive(archive, destination)
        return find_core_candidates(destination)
