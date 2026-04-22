"""Patch state endpoint — returns currently ingested TFT patch version."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/patch", tags=["patch"])


def _get_version_marker() -> Path | None:
    """Get the path to the cached version marker file."""
    marker = Path(settings.tft_cache_dir) / "latest_version.txt"
    if not marker.exists():
        return None
    return marker


@router.get("/current")
async def get_current_patch() -> dict:
    """Return the currently cached TFT patch version.
    
    Reads from ~/.tft-copilot/cache/latest_version.txt (or wherever
    settings.tft_cache_dir points).
    
    Returns:
        {"version": "17.1"} when a version has been ingested.
        {"version": None} when no version has been cached yet.
    """
    marker = _get_version_marker()
    if marker is None:
        return {"version": None}
    return {"version": marker.read_text(encoding="utf-8").strip()}
