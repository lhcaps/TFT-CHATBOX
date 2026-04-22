-- ============================================
-- TFT Local Copilot - Initial Schema
-- ============================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255),
    mode VARCHAR(16) NOT NULL DEFAULT 'normal',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Chunks table for RAG knowledge base
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    source VARCHAR(255) NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1024),
    fts tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source, content_hash)
);

-- Create HNSW index on embeddings
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Full-text search index on generated fts column
CREATE INDEX IF NOT EXISTS chunks_content_fts_idx ON chunks USING gin (fts);

-- Composite index for deduplication
CREATE INDEX IF NOT EXISTS chunks_source_hash_idx ON chunks (source, content_hash);

-- Sessions index
CREATE INDEX IF NOT EXISTS sessions_created_at_idx ON sessions (created_at DESC);

-- Messages index
CREATE INDEX IF NOT EXISTS messages_session_created_idx ON messages (session_id, created_at);

-- Hybrid search function (combines vector and full-text)
CREATE OR REPLACE FUNCTION hybrid_search_chunks(
    query_embedding VECTOR(1024),
    query_text TEXT,
    top_k INT DEFAULT 6
)
RETURNS TABLE (
    id INT,
    content TEXT,
    source VARCHAR(255),
    metadata JSONB,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH text_matches AS (
        SELECT id, content, source, metadata,
               ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) AS text_rank
        FROM chunks
        WHERE to_tsvector('english', content) @@ plainto_tsquery('english', query_text)
    ),
    vector_matches AS (
        SELECT id, 1 - (embedding <=> query_embedding) AS vector_similarity
        FROM chunks
    )
    SELECT
        c.id,
        c.content,
        c.source,
        c.metadata,
        COALESCE(v.vector_similarity, 0) * 0.7 + COALESCE(t.text_rank, 0) * 0.3 AS similarity
    FROM chunks c
    LEFT JOIN text_matches t ON c.id = t.id
    LEFT JOIN vector_matches v ON c.id = v.id
    ORDER BY similarity DESC
    LIMIT top_k;
END;
$$ LANGUAGE plpgsql;
