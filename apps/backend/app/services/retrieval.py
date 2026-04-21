"""RAG retrieval service using hybrid search (semantic + full-text)."""
from __future__ import annotations

from app.db import get_pool
from app.services.ollama import ollama


async def retrieve_chunks(query: str, top_k: int = 6) -> list[dict]:
    """Retrieve relevant chunks using hybrid search.

    Combines semantic (vector) and full-text search via hybrid_search_chunks SQL function.
    Returns chunks with source, heading, text, and relevance score.
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
            FROM hybrid_search_chunks($1::vector, $2, $3)
            """,
            embedding,
            query,
            top_k,
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
