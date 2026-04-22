"""Scrape Space Gods set overview + patch 17.1 full content and ingest into DB.

D-09: Ingest full patch 17.1 + Space Gods set overview into RAG.
URLs:
  - Set overview: https://teamfighttactics.leagueoflegends.com/en-us/set-overview/tft-set-17-space-gods/
  - Patch 17.1: https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/teamfight-tactics-patch-17-1/
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_pool
from app.services.ollama import ollama
from app.utils.hashing import content_hash

MAX_EMBEDDING_DIMS = 1024

# ─── URL Constants ──────────────────────────────────────────────────────────────

PATCH_17_1_URL = (
    "https://teamfighttactics.leagueoflegends.com/en-us/news/"
    "game-updates/teamfight-tactics-patch-17-1/"
)
SET_OVERVIEW_URL = (
    "https://teamfighttactics.leagueoflegends.com/en-us/set-overview/tft-set-17-space-gods/"
)
PATCH_NOTES_LISTING_URL = (
    "https://teamfighttactics.leagueoflegends.com/en-us/news/"
)


# ─── Fetch Helpers ─────────────────────────────────────────────────────────────

def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    r = httpx.get(url, timeout=30.0, headers=headers)
    r.raise_for_status()
    return r.text


def scrape_patch_url(patch_version: str) -> str:
    """Find patch notes URL for a given version (reused from scrape_patch17.py)."""
    parts = patch_version.split(".")
    major, minor = parts[0], parts[1] if len(parts) > 1 else "0"
    target_pattern = f"teamfight-tactics-patch-{major}-{minor}"

    try:
        html = fetch_page(PATCH_NOTES_LISTING_URL)
        pattern = re.compile(r'href="([^"]*teamfight-tactics-patch[^"]+)"')
        matches = pattern.findall(html)
        for href in matches:
            if target_pattern in href:
                if href.startswith("/"):
                    return f"https://teamfighttactics.leagueoflegends.com{href}"
                return href
    except Exception:
        pass

    template = (
        "https://teamfighttactics.leagueoflegends.com/en-us/news/"
        "game-updates/teamfight-tactics-patch-{major}-{minor}/"
    )
    return template.format(major=major, minor=minor)


# ─── Patch 17.1 Scraper ───────────────────────────────────────────────────────

def scrape_patch_17_1() -> list[dict]:
    """Scrape patch 17.1 page, return list of {section, content, source} dicts."""
    html = fetch_page(PATCH_17_1_URL)
    soup = BeautifulSoup(html, "lxml")
    main = soup.find("main")
    if not main:
        return []

    chunks = []
    current_section = "Header"

    for tag in main.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = tag.get_text(" ", strip=True)
        if not text or len(text) < 20:
            continue
        if tag.name in ("h1", "h2", "h3", "h4"):
            current_section = tag.get_text(" ", strip=True)
        else:
            # Build a markdown chunk per section
            slug = re.sub(r"[^a-z0-9]+", "_", current_section.lower())[:50]
            md = f"# {current_section}\n\n{text}"
            chunks.append({
                "title": current_section,
                "content": md,
                "source": f"riot:patch17.1:{slug}",
                "metadata": {
                    "season": "SET17",
                    "patch": "17.1",
                    "type": "patch_notes",
                    "source": "riot_official",
                    "section": current_section,
                },
            })
    return chunks


# ─── Space Gods Set Overview Scraper ──────────────────────────────────────────

def scrape_set_overview() -> list[dict]:
    """Scrape Space Gods set overview page.

    Extracts: champion names, traits, costs, trait descriptions, gods,
    artifacts, new mechanics, and system changes.
    """
    html = fetch_page(SET_OVERVIEW_URL)
    soup = BeautifulSoup(html, "lxml")
    main = soup.find("main") or soup.find("article") or soup.find("body")

    chunks = []
    current_section = "Set Overview"

    for tag in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "table"]):
        text = tag.get_text(" ", strip=True)
        if not text or len(text) < 30:
            continue

        if tag.name in ("h1", "h2", "h3", "h4"):
            current_section = tag.get_text(" ", strip=True)
        else:
            slug = re.sub(r"[^a-z0-9]+", "_", current_section.lower())[:50]
            md = f"# {current_section}\n\n{text}"
            chunks.append({
                "title": current_section,
                "content": md,
                "source": f"riot:set17:overview:{slug}",
                "metadata": {
                    "season": "SET17",
                    "patch": "17.1",
                    "type": "set_overview",
                    "source": "riot_official",
                    "section": current_section,
                },
            })

    return chunks


# ─── Space Gods Specific Content (dedicated chunks) ─────────────────────────────

def scrape_gods_content() -> list[dict]:
    """Scrape the Space Gods specific content sections.

    Creates dedicated chunks for: gods, artifacts, new traits, champion tiers.
    """
    html = fetch_page(SET_OVERVIEW_URL)
    soup = BeautifulSoup(html, "lxml")
    main = soup.find("main") or soup.find("article") or soup.find("body")

    chunks = []
    seen_sections = set()

    # Walk all sections looking for Space Gods specific content
    for tag in main.find_all(["h2", "h3", "h4"]):
        text = tag.get_text(" ", strip=True)
        text_lower = text.lower()

        # Only process meaningful sections
        if len(text) < 5:
            continue

        # Build a summary chunk from the heading + next sibling content
        section_content = []
        for sibling in tag.find_next_siblings():
            if sibling.name in ("h2", "h3", "h4"):
                break
            if sibling.name == "p":
                t = sibling.get_text(" ", strip=True)
                if t:
                    section_content.append(t)
            elif sibling.name == "li":
                t = sibling.get_text(" ", strip=True)
                if t:
                    section_content.append(f"- {t}")
            elif sibling.name == "table":
                rows = []
                for row in sibling.find_all("tr"):
                    cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
                    if cells:
                        rows.append(" | ".join(cells))
                if rows:
                    section_content.append("Table:\n" + "\n".join(rows))

        if not section_content:
            continue

        full_content = "\n\n".join(section_content)
        if len(full_content) < 50:
            continue

        slug = re.sub(r"[^a-z0-9]+", "_", text.lower())[:50]

        # Classify the section type
        text_lower = text.lower()
        if any(k in text_lower for k in ["god", "space god", "boon"]):
            content_type = "space_gods_gods"
        elif any(k in text_lower for k in ["artifact", "artifacts"]):
            content_type = "space_gods_artifacts"
        elif any(k in text_lower for k in ["trait", "traits", "groove", "mecha", "nova", "anima"]):
            content_type = "space_gods_traits"
        elif any(k in text_lower for k in ["champion", "unit", "cost"]):
            content_type = "space_gods_champions"
        elif any(k in text_lower for k in ["augment", "augments"]):
            content_type = "space_gods_augments"
        elif any(k in text_lower for k in ["item", "items", "artifact"]):
            content_type = "space_gods_items"
        else:
            content_type = "space_gods_general"

        chunks.append({
            "title": text,
            "content": f"# {text}\n\n{full_content}",
            "source": f"riot:set17:overview:{slug}",
            "metadata": {
                "season": "SET17",
                "patch": "17.1",
                "type": content_type,
                "source": "riot_official",
                "section": text,
            },
        })
        seen_sections.add(slug)

    return chunks


# ─── Database Ingestion ─────────────────────────────────────────────────────

async def ingest_into_db(chunks: list[dict]) -> dict:
    """Insert set overview chunks into DB with embeddings."""
    if not chunks:
        return {"ingested": 0, "skipped": 0, "total": 0}

    texts = [c["content"] for c in chunks]
    raw_embeddings = await ollama.generate_embeddings(texts)
    embeddings = [emb[:MAX_EMBEDDING_DIMS] for emb in raw_embeddings]
    hashes = [content_hash(t) for t in texts]

    pool = await get_pool()
    stats = {"ingested": 0, "skipped": 0, "total": len(chunks)}

    async with pool.acquire() as conn:
        for chunk, embedding, hash_ in zip(chunks, embeddings, hashes):
            existing = await conn.fetchval(
                "SELECT 1 FROM chunks WHERE source = $1 AND content_hash = $2",
                chunk["source"],
                hash_,
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
                hash_,
                chunk["source"],
                json.dumps(chunk["metadata"]),
                embedding_str,
            )
            stats["ingested"] += 1

    return stats


# ─── Public API ──────────────────────────────────────────────────────────────

async def scrape_and_ingest_patch17_1() -> dict:
    """Scrape patch 17.1 notes and ingest into DB."""
    chunks = scrape_patch_17_1()
    stats = await ingest_into_db(chunks)
    stats["source"] = "patch17.1"
    stats["chunks"] = len(chunks)
    return stats


async def scrape_and_ingest_set_overview() -> dict:
    """Scrape Space Gods set overview and ingest into DB."""
    # Get both overview + dedicated gods content
    overview_chunks = scrape_set_overview()
    gods_chunks = scrape_gods_content()
    all_chunks = overview_chunks + gods_chunks

    stats = await ingest_into_db(all_chunks)
    stats["source"] = "set_overview"
    stats["chunks"] = len(all_chunks)
    return stats


async def scrape_and_ingest_all() -> dict:
    """Scrape all Space Gods content (set overview + patch 17.1) and ingest into DB."""
    patch_stats = await scrape_and_ingest_patch17_1()
    overview_stats = await scrape_and_ingest_set_overview()

    return {
        "ingested": patch_stats["ingested"] + overview_stats["ingested"],
        "skipped": patch_stats["skipped"] + overview_stats["skipped"],
        "total": patch_stats["total"] + overview_stats["total"],
        "sources": {
            "patch17.1": patch_stats,
            "set_overview": overview_stats,
        },
    }


# ─── CLI Entry Point ──────────────────────────────────────────────────────

async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Space Gods set overview and patch 17.1")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scrape both set overview and patch 17.1 (default)",
    )
    parser.add_argument(
        "--set-overview",
        action="store_true",
        help="Scrape only Space Gods set overview",
    )
    parser.add_argument(
        "--patch-notes",
        action="store_true",
        help="Scrape only patch 17.1 notes",
    )
    args = parser.parse_args()

    if args.patch_notes:
        stats = await scrape_and_ingest_patch17_1()
        print(f"Patch 17.1: ingested={stats['ingested']}, skipped={stats['skipped']}, chunks={stats['chunks']}")
    elif args.set_overview:
        stats = await scrape_and_ingest_set_overview()
        print(f"Set Overview: ingested={stats['ingested']}, skipped={stats['skipped']}, chunks={stats['chunks']}")
    else:
        stats = await scrape_and_ingest_all()
        print(
            f"Total: ingested={stats['ingested']}, skipped={stats['skipped']}, "
            f"total={stats['total']} "
            f"(patch17.1: {stats['sources']['patch17.1']['chunks']} chunks, "
            f"set_overview: {stats['sources']['set_overview']['chunks']} chunks)"
        )


if __name__ == "__main__":
    asyncio.run(main())
