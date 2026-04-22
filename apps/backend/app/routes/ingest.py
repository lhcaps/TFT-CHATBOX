"""Data ingestion endpoints."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.middleware.auth import verify_api_key

router = APIRouter(prefix="/ingest", tags=["ingest"])
logger = logging.getLogger(__name__)


@router.post("/obsidian")
async def ingest_obsidian(_: str = Depends(verify_api_key)) -> dict:
    """Trigger Obsidian vault ingestion."""
    vault_path = settings.obsidian_vault_path
    if not vault_path:
        raise HTTPException(status_code=400, detail="OBSIDIAN_VAULT_PATH not set")
    if not Path(vault_path).exists():
        raise HTTPException(status_code=404, detail="Vault path not found")

    from scripts.ingest_obsidian import ingest_vault

    try:
        result = await ingest_vault(vault_path, settings.rag_chunk_size, settings.rag_chunk_overlap)
        return {"status": "ok", "result": result}
    except Exception as e:
        logger.exception("Obsidian ingest failed")
        raise HTTPException(status_code=500, detail="Ingestion failed — check server logs")


@router.post("/tft-static")
async def ingest_tft_static_route(
    patch: str | None = None,
) -> dict:
    """Trigger TFT static data ingestion.

    Args:
        patch: Optional patch version (e.g. "17.1"). If omitted, uses latest.
    """
    from scripts.ingest_tft_static import ingest_tft_static as do_ingest

    try:
        result = await do_ingest(patch=patch)
        return {"status": "ok", "result": result}
    except Exception as e:
        logger.exception("TFT static ingest failed")
        raise HTTPException(status_code=500, detail="Ingestion failed — check server logs")


@router.get("/tft-static/version")
async def get_tft_version() -> dict:
    """Get the current/latest TFT Data Dragon version and cached version."""
    from scripts.ingest_tft_static import (
        get_latest_version,
        get_cached_version,
        get_cache_dir,
    )

    latest = await get_latest_version()
    cached = await get_cached_version()
    cache_dir = str(get_cache_dir(latest)) if latest else None

    return {
        "latest": latest,
        "cached": cached,
        "cache_dir": str(Path(settings.tft_cache_dir)),
        "is_stale": latest != cached if latest and cached else True,
    }
