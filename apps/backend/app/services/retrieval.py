"""RAG retrieval service using hybrid search (semantic + full-text)."""
from __future__ import annotations

import json
import logging

from app.config import settings
from app.db import get_pool
from app.services.cache import CacheEntry, embedding_cache
from app.services.ollama import OllamaService, RetrievedChunk, ollama

logger = logging.getLogger(__name__)

# Embedding dimensions used in the database (HNSW index limit = 2000)
DB_EMBEDDING_DIMS = min(settings.ollama_embedding_dims, 1024)

# ─── Database Schema Migration (idempotent) ───────────────────────────────────
_MIGRATION_SQL = """
-- Add entity_type as a generated column from metadata JSONB (RAG2-01)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_columns
        WHERE tablename = 'document_chunks' AND attname = 'entity_type'
    ) THEN
        ALTER TABLE document_chunks
        ADD COLUMN entity_type text
        GENERATED ALWAYS AS (metadata->>'entity_type') STORED;
    END IF;
END
$$;

-- Create index for fast entity type filtering (RAG2-01)
CREATE INDEX IF NOT EXISTS idx_chunks_entity_type ON document_chunks(entity_type);

-- Create or replace enhanced hybrid search with entity_filter support (RAG2-01)
CREATE OR REPLACE FUNCTION hybrid_search_chunks_by_patch(
    query_embedding vector(1024),
    query_text text,
    top_k int,
    patch_filter text DEFAULT NULL,
    entity_filter text DEFAULT NULL
) RETURNS TABLE(id uuid, content text, source text, metadata jsonb, similarity float) AS $$
DECLARE
    semantic_rank int;
    fulltext_rank int;
BEGIN
    -- Semantic search: cosine similarity ranking
    WITH semantic AS (
        SELECT
            id,
            content,
            source,
            metadata,
            1 - (embedding <=> query_embedding) AS similarity,
            ROW_NUMBER() OVER (ORDER BY 1 - (embedding <=> query_embedding)) AS rn
        FROM document_chunks
        WHERE (patch_filter IS NULL OR (metadata->>'patch') = patch_filter)
          AND (entity_filter IS NULL OR (metadata->>'entity_type') = entity_filter)
    )
    SELECT rn INTO semantic_rank FROM semantic WHERE id = (SELECT id FROM semantic LIMIT 1);

    -- Full-text search: ts_rank ranking
    WITH full_text AS (
        SELECT
            id,
            content,
            source,
            metadata,
            ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) AS rank,
            ROW_NUMBER() OVER (ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) DESC) AS rn
        FROM document_chunks
        WHERE (patch_filter IS NULL OR (metadata->>'patch') = patch_filter)
          AND (entity_filter IS NULL OR (metadata->>'entity_type') = entity_filter)
          AND to_tsvector('english', content) @@ plainto_tsquery('english', query_text)
    )
    SELECT rn INTO fulltext_rank FROM full_text WHERE id = (SELECT id FROM full_text LIMIT 1);

    -- Return hybrid results with RRF fusion
    RETURN QUERY
    WITH hybrid AS (
        SELECT
            s.id,
            s.content,
            s.source,
            s.metadata,
            (
                COALESCE(
                    1.0 / (COALESCE(semantic_rank, 10000) + 2),
                    0
                ) +
                COALESCE(
                    1.0 / (COALESCE(fulltext_rank, 10000) + 2),
                    0
                )
            ) AS score
        FROM (
            SELECT id, content, source, metadata,
                ROW_NUMBER() OVER (ORDER BY 1 - (embedding <=> query_embedding)) AS rn
            FROM document_chunks
            WHERE (patch_filter IS NULL OR (metadata->>'patch') = patch_filter)
              AND (entity_filter IS NULL OR (metadata->>'entity_type') = entity_filter)
        ) s
        LEFT JOIN LATERAL (
            SELECT rn FROM (
                SELECT id,
                    ROW_NUMBER() OVER (ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) DESC) AS rn
                FROM document_chunks
                WHERE (patch_filter IS NULL OR (metadata->>'patch') = patch_filter)
                  AND (entity_filter IS NULL OR (metadata->>'entity_type') = entity_filter)
                  AND to_tsvector('english', content) @@ plainto_tsquery('english', query_text)
            ) ft
            WHERE ft.id = s.id
        ) ft ON true
        ORDER BY score DESC
        LIMIT top_k
    )
    SELECT h.id, h.content, h.source, h.metadata, h.score
    FROM hybrid h;
END;
$$ LANGUAGE plpgsql;
"""


async def _ensure_schema(pool) -> None:
    """Run schema migrations idempotently at startup."""
    try:
        async with pool.acquire() as conn:
            await conn.execute(_MIGRATION_SQL)
        logger.info("RAG2-01 schema migration: entity_type column + hybrid_search_chunks_by_patch(v5) applied")
    except Exception as e:
        logger.warning(f"RAG2-01 schema migration: {e}")


async def retrieve_chunks(
    query: str,
    mode: str = "rag",
    top_k: int = 6,
    patch: str | None = None,
    entity_filter: str | None = None,  # RAG2-01
) -> list[dict]:
    """Retrieve relevant chunks using hybrid search with optional entity filtering.

    Args:
        query: Search query text.
        mode: Search mode (normal, rag, coach). Used for cache key.
        top_k: Number of chunks to return (default 6).
        patch: Optional patch version to filter by (e.g. "17.1"). If None, searches all patches.
        entity_filter: Optional entity type to filter by (e.g. "champion", "item", "trait").
                      If None, returns all entity types. Per RAG2-01.
    """
    pool = await get_pool()

    # Ensure schema is up to date (idempotent, runs once)
    await _ensure_schema(pool)

    # Check cache first (cache key includes entity_filter)
    cached = embedding_cache.get(query, mode, patch, entity_filter)
    if cached is not None:
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
    embedding = raw_embedding[:DB_EMBEDDING_DIMS]

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                id,
                content,
                source,
                metadata,
                similarity
            FROM hybrid_search_chunks_by_patch($1::vector, $2, $3, $4, $5)
            """,
            json.dumps(embedding),
            query,
            top_k,
            patch,
            entity_filter,  # RAG2-01
        )

    # Convert to dicts for reranking (RAG2-02)
    chunks_dicts = [
        {
            "id": str(row["id"]),
            "content": row["content"],
            "source": row["source"],
            "metadata": json.loads(row["metadata"]) if isinstance(row["metadata"], str) else (row["metadata"] or {}),
            "score": float(row["similarity"]) if row["similarity"] is not None else 0.0,
        }
        for row in rows
    ]

    # Apply multi-factor reranking (RAG2-02)
    from app.services.ranking import rerank_chunks
    reranked = rerank_chunks(chunks_dicts, query=query)

    # Slice to top_k after reranking
    reranked = reranked[:top_k]

    # Store in cache (store full result, slice on retrieval)
    retrieved = [
        RetrievedChunk(
            id=chunk["id"],
            content=chunk["content"],
            source=chunk["source"],
            metadata=chunk["metadata"],
            similarity=chunk["score"],
        )
        for chunk in reranked
    ]
    embedding_cache.set(query, mode, patch, entity_filter, CacheEntry(embedding=embedding, chunks=retrieved))

    return reranked
