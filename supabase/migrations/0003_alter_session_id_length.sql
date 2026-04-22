-- Migration: alter_session_id_length
-- Fix: VARCHAR(16) too short for UUID session IDs (UUID = 36 chars)
--      Also fixes smoke test session IDs (e.g. "smoke-test-q1-normal" = 20 chars)

ALTER TABLE sessions
    ALTER COLUMN id TYPE VARCHAR(64);

ALTER TABLE messages
    ALTER COLUMN session_id TYPE VARCHAR(64);
