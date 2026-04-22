"""RAG retrieval service using hybrid search (semantic + full-text)."""
from __future__ import annotations

import json

from app.config import settings
from app.db import get_pool
from app.services.cache import CacheEntry, embedding_cache
from app.services.ollama import OllamaService, RetrievedChunk, ollama

# Embedding dimensions used in the database (HNSW index limit = 2000)
DB_EMBEDDING_DIMS = min(settings.ollama_embedding_dims, 1024)


async def retrieve_chunks(
    query: str,
    mode: str = "rag",
    top_k: int = 6,
    patch: str | None = None,
) -> list[dict]:
    """Retrieve relevant chunks using hybrid search.

    Args:
        query: Search query text.
        mode: Search mode (normal, rag, coach). Used for cache key.
        top_k: Number of chunks to return (default 6).
        patch: Optional patch version to filter by (e.g. "17.1"). If None, searches all patches.

    Returns:
        List of dicts with id, content, source, metadata, score.
    """
    # Check cache first
    cached = embedding_cache.get(query, mode, patch)
    if cached is not None:
        # Return chunks from cache, sliced to top_k
        return [
            {
                "id": str(chunk.id),
                "content": chunk.content,
                "source": chunk.source,
                "metadata": chunk.metadata or {},
                "score": chunk.similarity,
            }
            for chunk in cached.chunks[:top_k]
        ]

    # Cache miss — generate embedding and run search
    raw_embedding = await ollama.generate_embedding(query)
    # Truncate to DB column dimensions (qwen3-embedding:4b creates 2560 dims > DB limit of 1024)
    embedding = raw_embedding[:DB_EMBEDDING_DIMS]

    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                id,
                content,
                source,
                metadata,
                similarity
            FROM hybrid_search_chunks_by_patch($1::vector, $2, $3, $4)
            """,
            json.dumps(embedding),
            query,
            top_k,
            patch,
        )

    # Build RetrievedChunk list from rows
    chunks: list[RetrievedChunk] = [
        RetrievedChunk(
            id=str(row["id"]),
            content=row["content"],
            source=row["source"],
            metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else (row["metadata"] or {}),
            similarity=float(row["similarity"]) if row["similarity"] is not None else 0.0,
        )
        for row in rows
    ]

    # Store in cache (store full result, slice on retrieval)
    embedding_cache.set(query, mode, patch, CacheEntry(embedding=embedding, chunks=chunks))

    return [
        {
            "id": str(chunk.id),
            "content": chunk.content,
            "source": chunk.source,
            "metadata": chunk.metadata or {},
            "score": chunk.similarity,
        }
        for chunk in chunks[:top_k]
    ]
