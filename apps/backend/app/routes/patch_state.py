"""Patch state endpoints — reads from DB patch_info table."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.db import get_pool
from app.middleware.auth import verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/patch", tags=["patch"])


def _parse_patch(v: str) -> tuple[int, int]:
    """Parse patch version string into (major, minor) integers."""
    if not v:
        return (0, 0)
    parts = v.split(".")
    try:
        major = int(parts[0]) if parts else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        return (major, minor)
    except (ValueError, IndexError):
        return (0, 0)


@router.get("/current")
async def get_current_patch() -> dict:
    """Return the currently cached TFT patch version from DB.

    Returns:
        {"version": "17.1"} when a version has been set.
        {"version": null} when no version is set.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT current_patch FROM patch_info WHERE id = 1"
        )
    if row is None or not row["current_patch"]:
        return {"version": None}
    return {"version": row["current_patch"]}


@router.get("/status")
async def get_patch_status() -> dict:
    """Return full patch state from DB.

    Returns:
        {
            "current": "17.1",
            "latest_available": "17.1",
            "last_checked": "2026-04-22T...",
            "last_ingested": "2026-04-22T...",
            "is_stale": False,
            "ingest_status": "idle",
            "patch_notes_url": null
        }
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT current_patch, latest_available, last_checked, last_ingested,
                   ingest_status, patch_notes_url
            FROM patch_info WHERE id = 1
            """
        )
    if row is None:
        return {"error": "patch_info not initialized"}

    # Compare patch versions numerically (e.g. "17.1" > "16.8.1")
    current_parsed = _parse_patch(row["current_patch"] or "")
    latest_parsed = _parse_patch(row["latest_available"] or "")
    # Stale only when latest is numerically greater (newer patch available)
    is_stale = latest_parsed > current_parsed

    return {
        "current": row["current_patch"] or None,
        "latest_available": row["latest_available"] or None,
        "last_checked": row["last_checked"].isoformat() if row["last_checked"] else None,
        "last_ingested": row["last_ingested"].isoformat() if row["last_ingested"] else None,
        "is_stale": is_stale,
        "ingest_status": row["ingest_status"],
        "patch_notes_url": row["patch_notes_url"],
    }


@router.post("/status/refresh")
async def refresh_patch_status(
    patch: Optional[str] = None,
) -> dict:
    """Refresh latest_available from Riot CDN. Called by n8n workflow."""
    from scripts.ingest_tft_static import get_latest_version

    latest = patch
    if latest is None:
        try:
            latest = await get_latest_version()
        except Exception as e:
            return {"error": f"Failed to fetch latest: {e}"}

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE patch_info
            SET latest_available = $1, last_checked = NOW(), updated_at = NOW()
            WHERE id = 1
            """,
            latest,
        )
    return {"latest_available": latest}
