"""Data ingestion endpoints."""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import settings

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/obsidian")
async def ingest_obsidian() -> dict:
    """Trigger Obsidian vault ingestion."""
    vault_path = settings.obsidian_vault_path
    if not vault_path:
        raise HTTPException(status_code=400, detail="OBSIDIAN_VAULT_PATH not set")
    if not Path(vault_path).exists():
        raise HTTPException(status_code=404, detail="Vault path not found")

    from app.scripts.ingest_obsidian import ingest_vault

    try:
        result = await ingest_vault(vault_path, settings.rag_chunk_size)
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tft-static")
async def ingest_tft_static() -> dict:
    """Trigger TFT static data ingestion."""
    from app.scripts.ingest_tft_static import ingest_tft_static as do_ingest

    try:
        result = await do_ingest()
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
