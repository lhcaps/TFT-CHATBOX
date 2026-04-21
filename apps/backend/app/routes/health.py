"""Health check endpoint."""
from __future__ import annotations

import logging

import asyncpg
import httpx
from fastapi import APIRouter

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Verifies connectivity to both Ollama and Supabase.
    Returns JSON per D-20:
    {
        "ollama": "healthy|unreachable|error",
        "database": "healthy|unreachable"
    }
    """
    status: dict[str, str] = {
        "ollama": "unknown",
        "database": "unknown",
    }

    # Check Ollama connectivity
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            if response.status_code == 200:
                status["ollama"] = "healthy"
            else:
                status["ollama"] = "error"
    except httpx.ConnectError:
        status["ollama"] = "unreachable"
    except httpx.TimeoutException:
        status["ollama"] = "unreachable"
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        status["ollama"] = "unreachable"

    # Check Supabase connectivity
    try:
        conn = await asyncpg.connect(settings.database_url, timeout=5.0)
        await conn.fetchval("SELECT 1")
        await conn.close()
        status["database"] = "healthy"
    except ConnectionRefusedError:
        status["database"] = "unreachable"
    except asyncpg.PostgresConnectionError:
        status["database"] = "unreachable"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        status["database"] = "unreachable"

    return status
