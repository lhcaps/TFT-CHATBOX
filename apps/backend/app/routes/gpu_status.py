"""GPU / VRAM status endpoint via Ollama /api/ps."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx
from fastapi import APIRouter

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@dataclass
class GPUStatus:
    gpu_available: bool
    vram_used_mb: int | None
    vram_total_mb: int | None
    percent_used: int | None
    models_loaded: list[str]


async def _fetch_ollama_ps() -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{settings.ollama_base_url}/api/ps")
        resp.raise_for_status()
        return resp.json()


def _parse_gpu_status(ps_response: dict) -> GPUStatus:
    memory = ps_response.get("memory", {})
    models = ps_response.get("models", [])

    vram_used = memory.get("used")
    vram_total = memory.get("total")

    vram_used_mb: int | None = None
    vram_total_mb: int | None = None
    percent_used: int | None = None

    if vram_used is not None and vram_total is not None:
        vram_used_mb = round(vram_used / (1024 * 1024))
        vram_total_mb = round(vram_total / (1024 * 1024))
        if vram_total_mb > 0:
            percent_used = round((vram_used_mb / vram_total_mb) * 100)

    models_loaded = []
    for m in models:
        name = m.get("name")
        if name is None:
            model_val = m.get("model", "unknown")
            name = str(model_val)
        models_loaded.append(name)

    gpu_available = vram_total_mb is not None and vram_total_mb > 0

    return GPUStatus(
        gpu_available=gpu_available,
        vram_used_mb=vram_used_mb,
        vram_total_mb=vram_total_mb,
        percent_used=percent_used,
        models_loaded=models_loaded,
    )


@router.get("/gpu")
async def gpu_status() -> GPUStatus:
    try:
        ps_response = await _fetch_ollama_ps()
        return _parse_gpu_status(ps_response)
    except httpx.HTTPStatusError as e:
        logger.warning("Ollama /api/ps returned %s: %s", e.response.status_code, e.response.text)
        return GPUStatus(
            gpu_available=False,
            vram_used_mb=None,
            vram_total_mb=None,
            percent_used=None,
            models_loaded=[],
        )
    except Exception as e:
        logger.warning("Failed to fetch Ollama GPU status: %s", e)
        return GPUStatus(
            gpu_available=False,
            vram_used_mb=None,
            vram_total_mb=None,
            percent_used=None,
            models_loaded=[],
        )
