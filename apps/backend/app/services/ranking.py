"""Ranking service with multi-factor heuristic reranking (RAG2-02)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import settings, get_patch_priority

logger = logging.getLogger(__name__)


def get_recency_boost(ingested_at: str | None, weights: dict | None = None) -> float:
    """Compute recency boost based on when chunk was ingested.

    Args:
        ingested_at: ISO timestamp string (e.g., "2026-04-20T12:00:00Z")
        weights: recency_boost weights dict

    Returns:
        1.2 if ingested within 7 days, 1.0 if 7-30 days, 0.8 if older
    """
    if weights is None:
        weights = settings.ranking_weights.get("recency_boost", {})

    default_boost = float(weights.get("default", 0.8))
    if not ingested_at:
        return default_boost

    try:
        if ingested_at.endswith("Z"):
            dt = datetime.fromisoformat(ingested_at.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(ingested_at)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        days_ago = (now - dt).days

        if days_ago <= 7:
            return float(weights.get("7d", 1.2))
        elif days_ago <= 30:
            return float(weights.get("30d", 1.0))
        else:
            return default_boost
    except (ValueError, TypeError):
        return default_boost


def get_entity_priority(entity_type: str | None, weights: dict | None = None) -> float:
    """Get entity priority multiplier."""
    if weights is None:
        weights = settings.ranking_weights.get("entity_priority", {})
    if not entity_type:
        return 1.0
    return float(weights.get(str(entity_type), 1.0))


def rerank_chunks(chunks: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """Apply multi-factor heuristic reranking to chunks.

    Formula: final_score = cosine_similarity × patch_priority × entity_priority × recency_boost

    Args:
        chunks: List of chunk dicts with id, content, source, metadata, score
        query: Original search query (for logging only in this version)

    Returns:
        Sorted list of chunks with updated score field and _ranking debug metadata
    """
    if not chunks:
        return chunks

    weights = settings.ranking_weights

    for chunk in chunks:
        metadata = chunk.get("metadata", {})

        # 1. Cosine similarity (already in chunk.score)
        cosine = float(chunk.get("score", 0.0))

        # 2. Patch priority
        patch = metadata.get("patch")
        patch_prio = get_patch_priority(patch, weights.get("patch_priority"))

        # 3. Entity priority
        entity_type = metadata.get("entity_type")
        entity_prio = get_entity_priority(entity_type, weights.get("entity_priority"))

        # 4. Recency boost
        ingested_at = metadata.get("ingested_at")
        recency = get_recency_boost(ingested_at, weights.get("recency_boost"))

        # Compute final score
        final_score = cosine * patch_prio * entity_prio * recency

        # Attach ranking log for debugging
        chunk["_ranking"] = {
            "cosine": round(cosine, 4),
            "patch_priority": patch_prio,
            "entity_priority": entity_prio,
            "recency_boost": recency,
            "final_score": round(final_score, 4),
        }
        chunk["score"] = final_score

        # Log significant ranking decisions (deprioritized chunks)
        if patch_prio < 1.0 or entity_prio != 1.0 or recency != 1.0:
            logger.debug(
                f"Ranking: chunk={str(chunk.get('id', ''))[:8]}, "
                f"cosine={cosine:.3f}, patch_prio={patch_prio}, "
                f"entity_prio={entity_prio}, recency={recency}, "
                f"final={final_score:.3f}"
            )

    # Sort by final score descending
    return sorted(chunks, key=lambda c: float(c.get("score", 0)), reverse=True)
