import asyncio
import asyncpg
import httpx

async def test():
    # Check DB chunks
    pool = await asyncpg.create_pool('postgresql://postgres:postgres@localhost:54322/postgres', min_size=1, max_size=1)
    async with pool.acquire() as conn:
        rows = await conn.fetch('SELECT id, source FROM chunks LIMIT 5')
        print(f'Chunks in DB: {len(rows)}')
        for row in rows:
            print(f'  - {row["id"]}: {row["source"]}')

    # Test embedding dims
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post('http://localhost:11434/api/embed', json={
            'model': 'qwen3-embedding:4b',
            'input': ['best augments in patch 17.1'],
            'truncate': True
        })
        emb = r.json()['embeddings'][0]
        emb1024 = emb[:1024]
        print(f'Embedding dims: {len(emb)}, truncated to: {len(emb1024)}')

    await pool.close()

asyncio.run(test())
