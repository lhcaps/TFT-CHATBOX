"""Ingest TFT static data (champions, traits, items, augments) from Riot CDN with per-patch disk cache."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx

from app.config import settings
from app.db import get_pool
from app.services.ollama import ollama
from app.utils.hashing import content_hash


# CDN base URLs for Riot Data Dragon
CDN_BASE = "https://ddragon.leagueoflegends.com/cdn"
VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"

# Data types and their CDN paths
TFT_DATA_TYPES = {
    "champions": "data/en_US/tft/tft-champion.json",
    "traits": "data/en_US/tft/tft-trait.json",
    "items": "data/en_US/tft/tft-item.json",
    "augments": "data/en_US/tft/tft-augments.json",
}

# Cache file names per data type
CACHE_FILES = {
    "champions": "champions.json",
    "traits": "traits.json",
    "items": "items.json",
    "augments": "augments.json",
}


async def fetch_json(url: str) -> dict:
    """Fetch JSON data from a URL using httpx."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def fetch_json_safe(url: str) -> dict | None:
    """Fetch JSON data from a URL, returning None on error (e.g. 403 for retired TFT sets)."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


async def get_latest_version() -> str:
    """Fetch the latest TFT patch version from Riot CDN."""
    versions = await fetch_json(VERSIONS_URL)
    if not versions or not isinstance(versions, list):
        raise ValueError(f"Unexpected versions response: {versions}")
    return versions[0]


def get_cache_dir(patch: str) -> Path:
    """Get the cache directory for a specific patch."""
    return Path(settings.tft_cache_dir) / patch


def ensure_cache_dir(patch: str) -> Path:
    """Ensure the cache directory exists for a patch."""
    cache_dir = get_cache_dir(patch)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


async def get_latest_cached_version() -> str | None:
    """Get the latest cached version from disk, if any."""
    cache_root = Path(settings.tft_cache_dir)
    if not cache_root.exists():
        return None
    # Find the highest version directory by name order
    try:
        versions = sorted([d.name for d in cache_root.iterdir() if d.is_dir()], reverse=True)
        return versions[0] if versions else None
    except (OSError, ValueError):
        return None


async def download_patch_data(version: str) -> dict[str, dict]:
    """Download all available TFT static data for a specific version in parallel."""
    async with asyncio.TaskGroup() as tg:
        tasks = {
            data_type: tg.create_task(fetch_json_safe(f"{CDN_BASE}/{version}/{cdn_path}"))
            for data_type, cdn_path in TFT_DATA_TYPES.items()
        }
    return {
        data_type: task.result()
        for data_type, task in tasks.items()
        if task.result() is not None
    }


def save_patch_to_cache(patch: str, data: dict[str, dict]) -> None:
    """Save patch data to disk cache."""
    cache_dir = ensure_cache_dir(patch)
    for data_type, json_data in data.items():
        cache_file = cache_dir / CACHE_FILES[data_type]
        cache_file.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
    # Write version file
    (cache_dir / "version.txt").write_text(patch, encoding="utf-8")


def load_patch_from_cache(patch: str) -> dict[str, dict] | None:
    """Load patch data from disk cache. Returns None if not cached."""
    cache_dir = get_cache_dir(patch)
    if not cache_dir.exists():
        return None
    result = {}
    for data_type, filename in CACHE_FILES.items():
        cache_file = cache_dir / filename
        if not cache_file.exists():
            return None
        result[data_type] = json.loads(cache_file.read_text(encoding="utf-8"))
    return result


async def get_patch_data(patch: str | None = None) -> tuple[str, dict[str, dict]]:
    """
    Get patch data: cache-first, CDN fallback.

    If patch is None, fetches the latest version from CDN.
    Checks disk cache first; if not found, downloads from CDN and caches.
    """
    if patch is None:
        patch = await get_latest_version()

    # Try cache first
    cached_data = load_patch_from_cache(patch)
    if cached_data is not None:
        return patch, cached_data

    # Download from CDN
    data = await download_patch_data(patch)
    save_patch_to_cache(patch, data)
    return patch, data


def format_champion(champ: dict) -> str:
    """Format a champion entry as readable text."""
    name = champ.get("character_id", champ.get("name", "Unknown"))
    cost = champ.get("tier", "?")
    traits = champ.get("traits", [])
    traits_str = ", ".join(traits) if traits else "None"

    lines = [f"# {name}", f"Cost: {cost}", f"Traits: {traits_str}"]

    # Include stats if available
    stats = champ.get("stats", {})
    if stats:
        for stat_name, stat_value in stats.items():
            lines.append(f"{stat_name}: {stat_value}")

    return "\n".join(lines)


def format_trait(trait: dict) -> str:
    """Format a trait entry as readable text."""
    name = trait.get("name", trait.get("id", "Unknown"))
    desc = trait.get("description", trait.get("desc", ""))

    lines = [f"# {name}", desc]

    # Include set info if available
    if "sets" in trait:
        lines.append(f"Sets: {trait['sets']}")

    return "\n".join(lines)


def format_item(item: dict) -> str:
    """Format an item entry as readable text."""
    name = item.get("name", item.get("id", "Unknown"))
    desc = item.get("description", item.get("desc", ""))
    effects = item.get("effects", {})
    from_item = item.get("from", [])

    lines = [f"# {name}", desc]

    if effects:
        for key, value in effects.items():
            lines.append(f"{key}: {value}")

    if from_item:
        lines.append(f"Components: {', '.join(str(x) for x in from_item)}")

    return "\n".join(lines)


def format_augment(augment: dict) -> str:
    """Format an augment entry as readable text."""
    name = augment.get("name", augment.get("id", "Unknown"))
    desc = augment.get("description", augment.get("desc", ""))
    tier = augment.get("tier", "?")
    lines = [f"# {name}", f"Tier: {tier}", desc]

    return "\n".join(lines)


def parse_tft_data(data: dict, data_type: str) -> list[dict]:
    """Parse TFT JSON data into a list of individual entries."""
    if data_type == "champions":
        # Champions data is in "data" key as dict of character_id -> champ info
        data_obj = data.get("data", data)
        return [{"character_id": k, **v} for k, v in data_obj.items()]
    elif data_type == "traits":
        # Traits data is in "data" key as dict
        data_obj = data.get("data", data)
        return [{"id": k, **v} for k, v in data_obj.items()]
    elif data_type == "items":
        # Items data is in "data" key as dict
        data_obj = data.get("data", data)
        return [{"id": k, **v} for k, v in data_obj.items()]
    elif data_type == "augments":
        # Augments might be a list or in "data" key
        if isinstance(data, list):
            return data
        return data.get("data", [data])
    return []


def format_data_type(data: dict, data_type: str) -> str:
    """Format all entries of a data type as a single chunk."""
    entries = parse_tft_data(data, data_type)

    if data_type == "champions":
        formatted = [format_champion(e) for e in entries]
    elif data_type == "traits":
        formatted = [format_trait(e) for e in entries]
    elif data_type == "items":
        formatted = [format_item(e) for e in entries]
    elif data_type == "augments":
        formatted = [format_augment(e) for e in entries]
    else:
        formatted = [str(e) for e in entries]

    return "\n\n---\n\n".join(formatted)


async def ingest_tft_static(patch: str | None = None) -> dict:
    """
    Ingest TFT static data from CDN with disk caching.

    1. Determine patch version (latest from CDN or specified)
    2. Check disk cache for existing data
    3. Download from CDN if not cached
    4. Save to cache
    5. Parse and chunk data by type
    6. Generate embeddings and store in DB

    Args:
        patch: Specific patch version to ingest. If None, uses latest.

    Returns:
        Dict with stats: types processed, chunks created, patch version
    """
    # Get patch data (cache-first, CDN fallback)
    version, data = await get_patch_data(patch)

    pool = await get_pool()
    stats = {"patch": version, "types": 0, "chunks": 0, "new_chunks": 0}

    async with pool.acquire() as conn:
        for data_type in TFT_DATA_TYPES:
            if data_type not in data:
                continue

            # Format data as text
            text = format_data_type(data[data_type], data_type)
            chunk_hash = content_hash(text)

            # Check if already ingested
            source = f"tft_static:{data_type}:{version}"
            existing = await conn.fetchval(
                "SELECT 1 FROM chunks WHERE source = $1 AND content_hash = $2",
                source,
                chunk_hash,
            )

            if existing:
                stats["chunks"] += 1
                continue

            # Generate embedding
            embedding = await ollama.generate_embedding(text)

            # Extract season from patch (e.g., "17.1" -> "SET17")
            major = version.split(".")[0] if version else "SET0"
            season = f"SET{major}"

            # Insert into DB
            metadata = {
                "season": season,
                "patch": version,
                "type": data_type,
            }

            await conn.execute(
                """
                INSERT INTO chunks (content, content_hash, source, metadata, embedding)
                VALUES ($1, $2, $3, $4, $5::vector)
                ON CONFLICT (source, content_hash) DO NOTHING
                """,
                text,
                chunk_hash,
                source,
                metadata,
                embedding,
            )

            stats["types"] += 1
            stats["chunks"] += 1
            stats["new_chunks"] += 1

    return stats


if __name__ == "__main__":
    import sys

    patch_arg = sys.argv[1] if len(sys.argv) > 1 else None
    result = asyncio.run(ingest_tft_static(patch_arg))
    print(f"Ingested patch {result['patch']}: {result['types']} types, {result['chunks']} chunks ({result['new_chunks']} new)")
