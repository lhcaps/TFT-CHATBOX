-- ============================================
-- TFT Local Copilot - Seed Data
-- ============================================

-- Insert a sample session for testing
INSERT INTO sessions (id, title, mode)
VALUES ('sample01', 'Welcome Session', 'normal')
ON CONFLICT (id) DO NOTHING;
