"""RAG retrieval service."""
from __future__ import annotations

from app.db import get_pool
from app.services.ollama import ollama


async def retrieve_chunks(query: str, top_k: int = 6) -> list[dict]:
    """Retrieve relevant chunks from the knowledge base."""
    embedding = await ollama.generate_embedding(query)

    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, content, metadata, 1 - (embedding <=> $1::vector) AS similarity
            FROM chunks
            ORDER BY embedding <=> $1::vector
            LIMIT $2
            """,
            embedding,
            top_k,
        )

    return [
        {
            "id": str(row["id"]),
            "content": row["content"],
            "metadata": row["metadata"],
            "similarity": float(row["similarity"]),
        }
        for row in rows
    ]
