"""Scrape TFT patch notes from official Riot page and ingest into DB."""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_pool
from app.services.ollama import ollama
from app.utils.hashing import content_hash


# ─── URL Templates ────────────────────────────────────────────────────────────

PATCH_NOTES_LISTING_URL = "https://teamfighttactics.leagueoflegends.com/en-us/news/"
PATCH_NOTES_URL_TEMPLATE = (
    "https://teamfighttactics.leagueoflegends.com/en-us/news/"
    "game-updates/teamfight-tactics-patch-{major}-{minor}/"
)

# Default metadata
DEFAULT_SEASON = "SET17"


# ─── URL Discovery ────────────────────────────────────────────────────────────

def scrape_patch_url(patch_version: str) -> str | None:
    """Find the patch notes URL for a given patch version by scraping the listing page.

    Searches for URL pattern: /teamfight-tactics-patch-{major}-{minor}/
    Returns the full URL or None if not found (falls back to constructed URL).
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    # Parse major.minor from "17.1" -> "17", "1"
    parts = patch_version.split(".")
    major, minor = parts[0], parts[1] if len(parts) > 1 else "0"
    target_pattern = f"teamfight-tactics-patch-{major}-{minor}"

    try:
        r = httpx.get(PATCH_NOTES_LISTING_URL, timeout=30.0, headers=headers)
        r.raise_for_status()
    except Exception:
        # Fallback to constructed URL
        return PATCH_NOTES_URL_TEMPLATE.format(major=major, minor=minor)

    # Find all patch links
    pattern = re.compile(r'href="([^"]*teamfight-tactics-patch[^"]+)"')
    matches = pattern.findall(r.text)
    for href in matches:
        if target_pattern in href:
            if href.startswith("/"):
                full = f"https://teamfighttactics.leagueoflegends.com{href}"
            else:
                full = href
            # Ensure trailing slash (Riot redirects without it)
            if not full.endswith("/"):
                full += "/"
            return full

    # Fallback — always include trailing slash
    fallback = PATCH_NOTES_URL_TEMPLATE.format(major=major, minor=minor)
    return fallback if fallback.endswith("/") else fallback + "/"


# ─── Core Scraping ───────────────────────────────────────────────────────────

def scrape_patch_notes(url: str) -> dict[str, str]:
    """Scrape TFT patch notes from the given URL and return sections as {section_title: content}."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    r = httpx.get(url, timeout=30.0, headers=headers)
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


# ─── Formatting ───────────────────────────────────────────────────────────────

def format_as_markdown(
    sections: dict[str, str],
    patch: str,
    season: str = DEFAULT_SEASON,
) -> list[dict]:
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


# ─── Database Ingestion ──────────────────────────────────────────────────────

MAX_EMBEDDING_DIMS = 1024  # Match existing DB data + pgvector HNSW limit


async def ingest_into_db(chunks: list[dict], patch_version: str) -> dict:
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
            source = f"tft_patch_notes:{patch_version}:{chunk['title'][:50].replace(' ', '_')}"

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


# ─── Public API ──────────────────────────────────────────────────────────────

async def scrape_and_ingest(patch: Optional[str] = None) -> dict:
    """Scrape patch notes and ingest into DB.

    If patch is None, auto-detect latest from Riot CDN.

    Returns dict with ingested/skipped/total counts plus patch + patch_url.
    """
    from scripts.ingest_tft_static import get_latest_version

    if patch is None:
        patch = await get_latest_version()

    # Extract season from patch number (e.g. "17.1" -> "SET17")
    patch_int = int(patch.split(".")[0])
    SEASON_MAP = {14: "SET14", 15: "SET15", 16: "SET16", 17: "SET17"}
    season = SEASON_MAP.get(patch_int, f"SET{patch_int}")

    # Find patch URL
    patch_url = scrape_patch_url(patch)
    if not patch_url:
        raise RuntimeError(f"Could not find URL for patch {patch}")

    # Scrape
    sections = scrape_patch_notes(patch_url)
    if not sections:
        raise RuntimeError(f"No sections found on patch page: {patch_url}")

    # Format and ingest
    chunks = format_as_markdown(sections, patch, season)
    stats = await ingest_into_db(chunks, patch)
    stats["patch"] = patch
    stats["patch_url"] = patch_url
    return stats


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape TFT patch notes and ingest into DB"
    )
    parser.add_argument(
        "patch",
        nargs="?",
        default=None,
        help="Patch version (e.g. 17.1). Auto-detects if omitted.",
    )
    args = parser.parse_args()

    print(f"Scraping TFT Patch from Riot page...")
    stats = await scrape_and_ingest(args.patch)
    print(
        f"Done! patch={stats['patch']}, "
        f"url={stats.get('patch_url', 'N/A')}, "
        f"ingested={stats['ingested']}, "
        f"skipped={stats['skipped']}, "
        f"total={stats['total']}"
    )


if __name__ == "__main__":
    asyncio.run(main())
