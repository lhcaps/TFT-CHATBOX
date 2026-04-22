import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:54322/postgres')
    rows = await conn.fetch("""
        SELECT source, count(*) as cnt
        FROM chunks
        WHERE source LIKE 'tft_patch_notes%'
        GROUP BY source
        ORDER BY source
    """)
    for r in rows:
        print(f"{r['source']}: {r['cnt']} chunks")
    total = await conn.fetchval("SELECT count(*) FROM chunks WHERE source LIKE 'tft_patch_notes%'")
    print(f"Total patch notes chunks: {total}")
    await conn.close()

asyncio.run(check())
