-- ============================================
-- TFT Local Copilot - Patch-Aware Hybrid Search
-- ============================================

CREATE OR REPLACE FUNCTION hybrid_search_chunks_by_patch(
    p_embedding VECTOR(1024),
    p_text TEXT,
    p_top_k INT DEFAULT 6,
    p_patch TEXT DEFAULT NULL
)
RETURNS TABLE (
    id INT,
    content TEXT,
    source VARCHAR(255),
    metadata JSONB,
    similarity FLOAT
) AS $$
BEGIN
    IF p_patch IS NULL THEN
        -- No patch filter: use all chunks
        RETURN QUERY
        WITH text_matches AS (
            SELECT c.id, c.content, c.source, c.metadata,
                   ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', p_text)) AS text_rank
            FROM chunks c
            WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', p_text)
        ),
        vector_matches AS (
            SELECT c.id, 1 - (c.embedding <=> p_embedding) AS vector_similarity
            FROM chunks c
        )
        SELECT
            c.id, c.content, c.source, c.metadata,
            COALESCE(v.vector_similarity, 0) * 0.7 + COALESCE(t.text_rank, 0) * 0.3 AS similarity
        FROM chunks c
        LEFT JOIN text_matches t ON c.id = t.id
        LEFT JOIN vector_matches v ON c.id = v.id
        WHERE c.embedding IS NOT NULL
        ORDER BY similarity DESC
        LIMIT p_top_k;
    ELSE
        -- Patch filter: only chunks matching metadata->>'patch' = p_patch
        RETURN QUERY
        WITH text_matches AS (
            SELECT c.id, c.content, c.source, c.metadata,
                   ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', p_text)) AS text_rank
            FROM chunks c
            WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', p_text)
              AND c.metadata->>'patch' = p_patch
        ),
        vector_matches AS (
            SELECT c.id, 1 - (c.embedding <=> p_embedding) AS vector_similarity
            FROM chunks c
            WHERE c.embedding IS NOT NULL
              AND c.metadata->>'patch' = p_patch
        )
        SELECT
            c.id, c.content, c.source, c.metadata,
            COALESCE(v.vector_similarity, 0) * 0.7 + COALESCE(t.text_rank, 0) * 0.3 AS similarity
        FROM chunks c
        LEFT JOIN text_matches t ON c.id = t.id
        LEFT JOIN vector_matches v ON c.id = v.id
        WHERE c.embedding IS NOT NULL
          AND c.metadata->>'patch' = p_patch
        ORDER BY similarity DESC
        LIMIT p_top_k;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- B-tree index for patch metadata queries (speeds up WHERE metadata->>'patch' = $1)
CREATE INDEX IF NOT EXISTS chunks_patch_idx ON chunks ((metadata->>'patch'));
