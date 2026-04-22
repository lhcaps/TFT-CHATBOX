"""Scrape TFT patch 17.1 from official Riot page and ingest into DB."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_pool
from app.services.ollama import ollama
from app.utils.hashing import content_hash


PATCH_URL = "https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/teamfight-tactics-patch-17-1/"
PATCH_VERSION = "17.1"
SEASON = "SET17"


def scrape_patch_notes() -> dict[str, str]:
    """Scrape TFT patch 17.1 notes and return sections as {section_title: content}."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    r = httpx.get(PATCH_URL, timeout=30.0, headers=headers)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    main = soup.find("main")
    if not main:
        raise RuntimeError("Could not find <main> element on patch page")

    sections: dict[str, list[str]] = {}
    current = "Header"

    for tag in main.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = tag.get_text(" ", strip=True)
        if not text:
            continue
        if tag.name in ("h1", "h2", "h3", "h4"):
            current = tag.get_text(" ", strip=True)
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(text)

    # Merge into full section texts
    merged: dict[str, str] = {}
    for title, items in sections.items():
        merged[title] = "\n\n".join(items)

    return merged


def format_as_markdown(sections: dict[str, str], patch: str, season: str) -> list[dict]:
    """Format sections as markdown chunks with metadata."""
    chunks = []
    for title, content in sections.items():
        if len(content.strip()) < 50:
            continue
        md = f"# {title}\n\n{content}"
        chunks.append({
            "title": title,
            "content": md,
            "metadata": {
                "season": season,
                "patch": patch,
                "type": "patch_notes",
                "source": "riot_official",
            },
            "hash": None,  # filled by caller
        })
    return chunks


MAX_EMBEDDING_DIMS = 1024  # Match existing DB data + pgvector HNSW limit


async def ingest_into_db(chunks: list[dict]) -> dict:
    """Insert chunks into the database with embeddings."""
    if not chunks:
        return {"ingested": 0, "skipped": 0, "total": 0}

    # Generate embeddings
    texts = [c["content"] for c in chunks]
    raw_embeddings = await ollama.generate_embeddings(texts)

    # Truncate to MAX_EMBEDDING_DIMS (HNSW limit is 2000)
    embeddings = [emb[:MAX_EMBEDDING_DIMS] for emb in raw_embeddings]

    # Hash
    for c in chunks:
        c["hash"] = content_hash(c["content"])

    # Insert
    pool = await get_pool()
    stats = {"ingested": 0, "skipped": 0, "total": len(chunks)}

    async with pool.acquire() as conn:
        for chunk, embedding in zip(chunks, embeddings):
            source = f"tft_patch_notes:{PATCH_VERSION}:{chunk['title'][:50].replace(' ', '_')}"

            existing = await conn.fetchval(
                "SELECT 1 FROM chunks WHERE source = $1 AND content_hash = $2",
                source,
                chunk["hash"],
            )
            if existing:
                stats["skipped"] += 1
                continue

            embedding_str = json.dumps(embedding)

            await conn.execute(
                """
                INSERT INTO chunks (content, content_hash, source, metadata, embedding)
                VALUES ($1, $2, $3, $4::jsonb, $5::vector)
                ON CONFLICT (source, content_hash) DO NOTHING
                """,
                chunk["content"],
                chunk["hash"],
                source,
                json.dumps(chunk["metadata"]),
                embedding_str,
            )
            stats["ingested"] += 1

    return stats


async def main() -> None:
    print(f"Scraping TFT Patch {PATCH_VERSION} from official Riot page...")
    sections = scrape_patch_notes()
    print(f"Found {len(sections)} sections: {list(sections.keys())}")

    chunks = format_as_markdown(sections, PATCH_VERSION, SEASON)
    print(f"Created {len(chunks)} chunks")

    print("Generating embeddings and ingesting into database...")
    stats = await ingest_into_db(chunks)
    print(f"Done! ingested={stats['ingested']}, skipped={stats['skipped']}, total={stats['total']}")


if __name__ == "__main__":
    asyncio.run(main())
