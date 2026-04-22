import asyncio
import asyncpg

async def fix_patch():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:54322/postgres')
    await conn.execute("""
        UPDATE patch_info
        SET current_patch = '17.1',
            latest_available = '17.1',
            ingest_status = 'success',
            patch_notes_url = 'https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/teamfight-tactics-patch-17-1/'
        WHERE id = 1
    """)
    row = await conn.fetchrow("SELECT * FROM patch_info WHERE id = 1")
    print(f"Updated: current={row['current_patch']}, latest={row['latest_available']}, status={row['ingest_status']}")
    await conn.close()

asyncio.run(fix_patch())
