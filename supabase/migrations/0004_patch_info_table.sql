-- ============================================
-- TFT Local Copilot - Patch Info Table
-- ============================================

-- Patch state table as single source of truth
CREATE TABLE IF NOT EXISTS patch_info (
    id SERIAL PRIMARY KEY,
    current_patch VARCHAR(16) NOT NULL DEFAULT '',
    latest_available VARCHAR(16) NOT NULL DEFAULT '',
    last_checked TIMESTAMPTZ,
    last_ingested TIMESTAMPTZ,
    ingest_status VARCHAR(32) DEFAULT 'idle',  -- idle | running | success | failed
    ingest_error TEXT,
    patch_notes_url TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed with current state (patch 17.1)
INSERT INTO patch_info (id, current_patch, latest_available, last_checked, last_ingested, ingest_status)
VALUES (1, '17.1', '17.1', NOW(), NOW(), 'success')
ON CONFLICT (id) DO NOTHING;

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS patch_info_updated_idx ON patch_info (updated_at DESC);
