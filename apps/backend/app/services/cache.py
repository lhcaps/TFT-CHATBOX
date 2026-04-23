"""Embedding cache with TTL-based LRU eviction."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from cachetools import TTLCache

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.ollama import RetrievedChunk

# ─── Constants ─────────────────────────────────────────────────────────────────

MAX_QUERY_LENGTH = 512  # Truncate queries longer than this to avoid large cache keys


@dataclass
class CacheEntry:
    """A cached retrieval result."""
    embedding: list[float]
    chunks: list["RetrievedChunk"]


def _make_cache_key(query: str, mode: str, patch: str | None, entity_filter: str | None) -> str:
    """Build a cache key from query, mode, patch, and optional entity_filter.

    Query is truncated to MAX_QUERY_LENGTH to prevent unbounded key sizes.
    """
    patch_part = patch if patch else "all"
    entity_part = entity_filter if entity_filter else "all"
    truncated = query[:MAX_QUERY_LENGTH] if len(query) > MAX_QUERY_LENGTH else query
    return f"{mode}:{patch_part}:{entity_part}:{truncated}"


class EmbeddingCache:
    """TTL-LRU cache for query embeddings and retrieval results.

    Key = (query_text, mode, patch). Stores both the embedding vector
    and the retrieved chunks so cache hits skip both Ollama AND the SQL query.
    """

    def __init__(self, max_size: int = 500, ttl_seconds: int = 1800) -> None:
        self._embedding_cache: TTLCache[str, CacheEntry] = TTLCache(
            maxsize=max_size, ttl=ttl_seconds
        )

    def get(self, query: str, mode: str, patch: str | None, entity_filter: str | None = None) -> CacheEntry | None:
        """Return cached entry for (query, mode, patch, entity_filter), or None if not found or expired."""
        key = _make_cache_key(query, mode, patch, entity_filter)
        return self._embedding_cache.get(key)  # type: ignore[return-value]

    def set(self, query: str, mode: str, patch: str | None, entity_filter: str | None, entry: CacheEntry) -> None:
        """Store an entry in the cache."""
        key = _make_cache_key(query, mode, patch, entity_filter)
        self._embedding_cache[key] = entry

    def clear(self) -> None:
        """Evict all entries from the cache."""
        self._embedding_cache.clear()


# Singleton instance — one cache per worker process
embedding_cache = EmbeddingCache()
