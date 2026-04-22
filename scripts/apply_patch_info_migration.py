"""Apply patch_info migration directly using asyncpg."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

import asyncpg


MIGRATION = """
CREATE TABLE IF NOT EXISTS patch_info (
    id SERIAL PRIMARY KEY,
    current_patch VARCHAR(16) NOT NULL DEFAULT '',
    latest_available VARCHAR(16) NOT NULL DEFAULT '',
    last_checked TIMESTAMPTZ,
    last_ingested TIMESTAMPTZ,
    ingest_status VARCHAR(32) NOT NULL DEFAULT 'idle',
    ingest_error TEXT,
    patch_notes_url TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO patch_info (id, current_patch, latest_available, last_checked, last_ingested, ingest_status)
VALUES (1, '17.1', '17.1', NOW(), NOW(), 'success')
ON CONFLICT (id) DO NOTHING;

CREATE INDEX IF NOT EXISTS patch_info_updated_idx ON patch_info (updated_at DESC);
"""


async def main():
    DATABASE_URL = "postgresql://postgres:postgres@localhost:54322/postgres"
    print("Connecting to database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Make sure Supabase local is running and DATABASE_URL is correct.")
        return

    print("Connected. Applying migration...")

    # Check if table exists
    exists = await conn.fetchval(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'patch_info')"
    )
    if exists:
        print("patch_info table already exists. Checking columns...")
        cols = await conn.fetch(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'patch_info' ORDER BY ordinal_position"
        )
        print(f"  Existing columns: {[c['column_name'] for c in cols]}")
    else:
        print("Creating patch_info table...")
        await conn.execute(MIGRATION)
        print("Migration applied successfully!")

    # Verify
    row = await conn.fetchrow("SELECT * FROM patch_info WHERE id = 1")
    if row:
        print(f"  Seed row: id={row['id']}, current_patch={row['current_patch']}, "
              f"latest={row['latest_available']}, status={row['ingest_status']}")
    else:
        print("WARNING: Seed row not found!")

    await conn.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
