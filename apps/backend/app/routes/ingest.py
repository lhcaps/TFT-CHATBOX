"""Data ingestion endpoints."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.middleware.auth import verify_api_key
from app.graph.events import trigger_reload

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
        trigger_reload()
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


@router.post("/patch-notes")
async def ingest_patch_notes_route(
    patch: str | None = None,
    _: str = Depends(verify_api_key),
) -> dict:
    """Scrape TFT patch notes from Riot and ingest into DB.

    Args:
        patch: Optional patch version (e.g. "17.1"). If omitted, uses latest from DB or CDN.

    Scrape flow:
    1. Get patch version (param or latest_available from patch_info or CDN)
    2. Find patch URL via listing page scrape or URL pattern
    3. Scrape content with BeautifulSoup
    4. Chunk, embed, and ingest into chunks table
    5. Update patch_info: current_patch + last_ingested + patch_notes_url
    """
    from scripts.scrape_patch17 import scrape_and_ingest

    from app.db import get_pool

    # Resolve patch version: use explicit param > current_patch > latest_available > CDN fallback
    resolved_patch = patch
    if resolved_patch is None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT current_patch, latest_available FROM patch_info WHERE id = 1"
            )
            if row and row["current_patch"]:
                resolved_patch = row["current_patch"]
            elif row and row["latest_available"]:
                resolved_patch = row["latest_available"]

    if resolved_patch is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "No patch version available. Pass ?patch=X.Y or set latest_available in DB."
            ),
        )

    # Update status to running
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE patch_info
            SET ingest_status = 'running', ingest_error = NULL, updated_at = NOW()
            WHERE id = 1
            """
        )

    try:
        stats = await scrape_and_ingest(resolved_patch)

        # Update patch_info on success
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE patch_info
                SET current_patch = $1,
                    latest_available = $1,
                    last_ingested = NOW(),
                    ingest_status = 'success',
                    ingest_error = NULL,
                    patch_notes_url = $2,
                    updated_at = NOW()
                WHERE id = 1
                """,
                resolved_patch,
                stats.get("patch_url"),
            )
        trigger_reload()
        return {"status": "ok", "patch": resolved_patch, **stats}
    except Exception as e:
        logger.exception("Patch notes ingest failed")
        # Update status to failed
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE patch_info
                SET ingest_status = 'failed', ingest_error = $1, updated_at = NOW()
                WHERE id = 1
                """,
                str(e)[:500],
            )
        raise HTTPException(
            status_code=500,
            detail=f"Patch notes ingest failed: {e}",
        )


@router.post("/metatft")
async def ingest_metatft_route(
    source: str | None = None,
    patch: str | None = None,
) -> dict:
    """Ingest MetaTFT comps and/or Space Gods set overview.

    Args:
        source: What to ingest — "comps" | "set-overview" | "patch" | "all" (default "all")
        patch: Optional patch version for comps (e.g. "17.1")

    D-05: POST /api/ingest/metatft endpoint
    D-06: Calls both metatft scraper and set overview scraper
    """
    from scripts.scrape_metatft import scrape_and_ingest as scrape_metatft
    from scripts.scrape_set_overview import scrape_and_ingest_all as scrape_set_overview_all

    source_mode = source or "all"
    stats = {}

    try:
        if source_mode in ("comps", "all"):
            metatft_stats = await scrape_metatft(patch=patch)
            stats["metatft"] = metatft_stats

        if source_mode in ("set-overview", "patch", "all"):
            # "patch" = set-overview + patch17.1 notes (all Space Gods content)
            set_stats = await scrape_set_overview_all()
            stats["set_overview"] = set_stats

        result = {
            "status": "ok",
            "source": source_mode,
            "patch": patch,
            "stats": stats,
            "total_ingested": sum(
                s.get("ingested", 0) for s in stats.values()
            ),
            "total_skipped": sum(
                s.get("skipped", 0) for s in stats.values()
            ),
        }
        trigger_reload()
        return result
    except Exception as e:
        logger.exception("MetaTFT ingest failed")
        raise HTTPException(
            status_code=500,
            detail=f"MetaTFT ingest failed: {e}",
        )


@router.post("/tft-set17")
async def ingest_tft_set17_route() -> dict:
    """Ingest the TFT Set 17 / Patch 17.1 clean data pack into the RAG DB.

    Loads tft_set17_patch17_1_data_pack.json and converts each section into
    Markdown chunks with embeddings, upserting into the chunks table with
    source='tft_set17'.

    Sections ingested:
    - Systems (Realm of the Gods, 9 Space Gods, Patch 17.1B changes)
    - Origins (all 17 Set 17 origins with champions + summaries)
    - Classes (all 13 Set 17 classes)
    - Champions (54 champions with cost + traits)
    - Items (standard, Radiant, Psionic, Anima, Artifacts)
    - Meta comps (12 S-tier + 8 A-tier comp snapshots)
    """
    from scripts.ingest_tft_set17 import ingest_all as do_ingest

    try:
        result = await do_ingest()
        trigger_reload()
        return {"status": "ok", "source": "tft_set17", **result}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("TFT Set 17 ingest failed")
        raise HTTPException(
            status_code=500,
            detail=f"TFT Set 17 ingest failed: {e}",
        )
