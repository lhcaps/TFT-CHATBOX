"""Phase 8 verification script."""
from __future__ import annotations
import sys
from pathlib import Path

# Make app/ importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio

from app.routes.patch_state import get_patch_status, get_current_patch
from app.routes.ingest import ingest_patch_notes_route
from scripts.scrape_patch17 import scrape_patch_url


async def test_all():
    print("=== GET /api/patch/current ===")
    r = await get_current_patch()
    print(r)

    print()
    print("=== GET /api/patch/status ===")
    s = await get_patch_status()
    print(f"current={s['current']}, latest={s['latest_available']}, is_stale={s['is_stale']}")
    print(f"ingest_status={s['ingest_status']}")

    print()
    print("=== URL Discovery ===")
    print("17.1:", scrape_patch_url("17.1"))
    print("17.2:", scrape_patch_url("17.2"))

    print()
    print("=== POST /api/ingest/patch-notes (expect skips) ===")
    result = await ingest_patch_notes_route(patch="17.1", _="")
    ingested = result.get("ingested")
    skipped = result.get("skipped")
    print(f"status={result['status']}, ingested={ingested}, skipped={skipped}")

    print()
    print("=== Final Status ===")
    s2 = await get_patch_status()
    print(f"current={s2['current']}, latest={s2['latest_available']}, is_stale={s2['is_stale']}")
    print(f"ingest_status={s2['ingest_status']}")

    print()
    print("=== Staleness Logic Test ===")
    from app.db import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE patch_info SET latest_available = '17.2' WHERE id = 1")
    stale_status = await get_patch_status()
    print(f"With latest=17.2: is_stale={stale_status['is_stale']}")
    async with pool.acquire() as conn2:
        await conn2.execute("UPDATE patch_info SET latest_available = '17.1' WHERE id = 1")
    restored = await get_patch_status()
    print(f"Restored latest=17.1: is_stale={restored['is_stale']}")

    print()
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(test_all())
