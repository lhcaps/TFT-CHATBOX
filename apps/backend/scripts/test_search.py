import asyncio
import asyncpg
import httpx
import json

async def test_search():
    # Get embedding
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post('http://localhost:11434/api/embed', json={
            'model': 'qwen3-embedding:4b',
            'input': ['best augments in patch 17.1'],
            'truncate': True
        })
        emb = r.json()['embeddings'][0][:1024]  # truncate to 1024

    # Test hybrid search function
    pool = await asyncpg.create_pool('postgresql://postgres:postgres@localhost:54322/postgres', min_size=1, max_size=1)
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                'SELECT id, source, LEFT(content, 80) as content FROM hybrid_search_chunks_by_patch($1::vector, $2, $3, $4)',
                json.dumps(emb),
                'best augments in patch 17.1',
                6,
                None
            )
            print(f'Search returned {len(rows)} rows')
            for row in rows:
                print(f'  - [{row["id"]}] {row["source"]}: {row["content"]}')
        except Exception as e:
            print(f'Error: {e}')
            import traceback; traceback.print_exc()

    await pool.close()

asyncio.run(test_search())
