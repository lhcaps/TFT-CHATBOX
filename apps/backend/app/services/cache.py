"""Embedding cache with TTL-based LRU eviction."""

from __future__ import annotations

from dataclasses import dataclass

from cachetools import TTLCache

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.ollama import RetrievedChunk


@dataclass
class CacheEntry:
    """A cached retrieval result."""
    embedding: list[float]
    chunks: list["RetrievedChunk"]


def _make_cache_key(query: str, mode: str, patch: str | None) -> str:
    """Build a cache key from query, mode, and optional patch filter."""
    patch_part = patch if patch else "all"
    return f"{mode}:{patch_part}:{query}"


class EmbeddingCache:
    """TTL-LRU cache for query embeddings and retrieval results.

    Key = (query_text, mode, patch). Stores both the embedding vector
    and the retrieved chunks so cache hits skip both Ollama AND the SQL query.
    """

    def __init__(self, max_size: int = 500, ttl_seconds: int = 1800) -> None:
        self._embedding_cache: TTLCache[str, CacheEntry] = TTLCache(
            maxsize=max_size, ttl=ttl_seconds
        )

    def get(self, query: str, mode: str, patch: str | None) -> CacheEntry | None:
        """Return cached entry for (query, mode, patch), or None if not found or expired."""
        key = _make_cache_key(query, mode, patch)
        return self._embedding_cache.get(key)  # type: ignore[return-value]

    def set(self, query: str, mode: str, patch: str | None, entry: CacheEntry) -> None:
        """Store an entry in the cache."""
        key = _make_cache_key(query, mode, patch)
        self._embedding_cache[key] = entry

    def clear(self) -> None:
        """Evict all entries from the cache."""
        self._embedding_cache.clear()


# Singleton instance — one cache per worker process
embedding_cache = EmbeddingCache()
