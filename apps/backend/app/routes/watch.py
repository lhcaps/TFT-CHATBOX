"""API endpoints for Obsidian file watcher (RAG2-05)."""
from __future__ import annotations

import logging
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.services.watcher import FileSystemWatcher

router = APIRouter(prefix="/watch", tags=["watch"])
logger = logging.getLogger(__name__)


class WatchStartRequest(BaseModel):
    vault_path: str | None = None  # If None, uses settings.obsidian_vault_path


class WatchStatusResponse(BaseModel):
    watching: bool
    vault_path: str | None = None
    started_at: str | None = None
    events_count: int = 0
    last_event: dict | None = None


@router.post("/start")
async def watch_start(request: WatchStartRequest | None = None) -> dict:
    """Start watching the Obsidian vault for file changes.

    After 500ms debounce, changes trigger reactive re-ingest.
    """
    watcher = FileSystemWatcher.get_instance()

    vault_path = request.vault_path if request else None
    if not vault_path:
        vault_path = settings.obsidian_vault_path

    if not vault_path:
        raise HTTPException(
            status_code=400,
            detail="No vault_path provided and OBSIDIAN_VAULT_PATH not set",
        )

    try:
        result = watcher.start(vault_path)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to start watcher")
        raise HTTPException(status_code=500, detail=f"Failed to start watcher: {e}")


@router.post("/stop")
async def watch_stop() -> dict:
    """Stop watching the Obsidian vault."""
    watcher = FileSystemWatcher.get_instance()
    return watcher.stop()


@router.get("/status")
async def watch_status() -> WatchStatusResponse:
    """Get current watcher status."""
    watcher = FileSystemWatcher.get_instance()
    return WatchStatusResponse(**watcher.get_status())


@router.get("/events")
async def watch_events(limit: int = 20) -> dict:
    """Get recent watcher events."""
    watcher = FileSystemWatcher.get_instance()
    events = watcher.event_log[-limit:]
    return {
        "events": events,
        "total": len(watcher.event_log),
    }
