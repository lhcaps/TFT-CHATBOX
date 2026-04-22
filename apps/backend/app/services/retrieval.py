"""RAG retrieval service using hybrid search (semantic + full-text)."""
from __future__ import annotations

from app.db import get_pool
from app.services.ollama import ollama


async def retrieve_chunks(query: str, top_k: int = 6, patch: str | None = None) -> list[dict]:
    """Retrieve relevant chunks using hybrid search.

    Args:
        query: Search query text.
        top_k: Number of chunks to return (default 6).
        patch: Optional patch version to filter by (e.g. "17.1"). If None, searches all patches.

    Returns:
        List of dicts with id, content, source, metadata, score.
    """
    embedding = await ollama.generate_embedding(query)

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
            embedding,
            query,
            top_k,
            patch,
        )

    return [
        {
            "id": str(row["id"]),
            "content": row["content"],
            "source": row["source"],
            "metadata": row["metadata"] or {},
            "score": float(row["similarity"]) if row["similarity"] is not None else 0.0,
        }
        for row in rows
    ]
