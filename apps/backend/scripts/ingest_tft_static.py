"""Ingest TFT static data (champions, traits, items, augments) from Riot CDN with per-patch disk cache."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TypedDict

import httpx

from app.config import settings
from app.db import get_pool
from app.services.ollama import ollama
from app.utils.hashing import content_hash


class TFTStaticData(TypedDict):
    champions: dict
    traits: dict
    items: dict
    augments: dict


# CDN base URLs for Riot Data Dragon
CDN_BASE = "https://ddragon.leagueoflegends.com/cdn"
VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"

# CommunityDragon fallback (for recent sets not yet on ddragon)
CDRAGON_BASE = "https://raw.communitydragon.org/latest/cdragon/tft"

# Default User-Agent to avoid 403 from Riot CDN
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

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


async def fetch_json(url: str, headers: dict | None = None) -> dict:
    """Fetch JSON data from a URL using httpx with browser User-Agent."""
    async with httpx.AsyncClient(timeout=30.0, headers=headers or DEFAULT_HEADERS) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def fetch_json_safe(url: str) -> dict | None:
    """Fetch JSON data from a URL, returning None on error (e.g. 403 for retired TFT sets)."""
    try:
        async with httpx.AsyncClient(timeout=30.0, headers=DEFAULT_HEADERS) as client:
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


def _get_cached_version_marker() -> Path | None:
    """Get the path to the cached version marker file."""
    marker = Path(settings.tft_cache_dir) / "latest_version.txt"
    if not marker.exists():
        return None
    return marker


async def get_cached_version() -> str | None:
    """Get the latest cached version from the marker file."""
    marker = _get_cached_version_marker()
    if marker is None:
        return None
    return marker.read_text(encoding="utf-8").strip()


async def save_cached_version(version: str) -> None:
    """Save the latest cached version to the marker file."""
    ensure_cache_dir(version)
    marker = Path(settings.tft_cache_dir) / "latest_version.txt"
    marker.write_text(version, encoding="utf-8")


def _extract_season_from_patch(patch: str) -> str:
    """Infer the TFT set/season from the patch number.

    TFT patch 17.x = Set 17 (Space Gods).
    Update this mapping as new sets are released.
    """
    patch_int = int(patch.split(".")[0])
    SEASON_MAP = {
        14: "SET14",
        15: "SET15",
        16: "SET16",
        17: "SET17",
    }
    return SEASON_MAP.get(patch_int, f"SET{patch_int}")


def _format_champions(data: dict, patch: str) -> str:
    """Format champion data as readable markdown."""
    lines = [f"# TFT Champions (Patch {patch})\n"]
    champions = data.get("data", {})
    for key, champ in sorted(champions.items(), key=lambda x: x[1].get("cost", 0)):
        name = champ.get("name", key)
        cost = champ.get("cost", "?")
        traits = champ.get("traits", [])
        stats = champ.get("stats", {})

        lines.append(f"## {name} (Cost: {cost})")
        if traits:
            lines.append(f"Traits: {', '.join(traits)}")
        if stats:
            hp = stats.get("hp", "?")
            attack_damage = stats.get("attackDamage", "?")
            ability_power = stats.get("abilityPower", "?")
            attack_speed = stats.get("attackSpeed", "?")
            crit = stats.get("critChance", "?")
            mana = stats.get("mana", "?")
            lines.append(
                f"Stats: HP: {hp} | AD: {attack_damage} | AP: {ability_power} "
                f"| AS: {attack_speed} | Crit: {crit}% | Mana: {mana}"
            )
        lines.append("")
    return "\n".join(lines)


def _format_traits(data: dict, patch: str) -> str:
    """Format trait data as readable markdown."""
    lines = [f"# TFT Traits (Patch {patch})\n"]
    traits = data.get("data", {})
    for key, trait in sorted(traits.items(), key=lambda x: x[1].get("name", "")):
        name = trait.get("name", key)
        desc = trait.get("desc", "")
        sets = trait.get("sets", [])

        lines.append(f"## {name}")
        if desc:
            lines.append(f"Desc: {desc}")
        for s in sets:
            min_u = s.get("minUnits", "?")
            max_u = s.get("maxUnits", "?")
            effects = s.get("effects", [])
            lines.append(f"Threshold {min_u}-{max_u} units:")
            for eff in effects:
                lines.append(f"  - {eff}")
        lines.append("")
    return "\n".join(lines)


def _format_items(data: dict, patch: str) -> str:
    """Format item data as readable markdown."""
    lines = [f"# TFT Items (Patch {patch})\n"]
    items = data.get("data", {})
    for key, item in sorted(items.items(), key=lambda x: x[1].get("name", "")):
        name = item.get("name", key)
        desc = item.get("desc", "")
        effects = item.get("effects", {})

        lines.append(f"## {name}")
        if desc:
            lines.append(f"Desc: {desc}")
        if effects:
            eff_str = " | ".join(f"{k}: {v}" for k, v in effects.items())
            lines.append(f"Effects: {eff_str}")
        lines.append("")
    return "\n".join(lines)


def _format_augments(data: dict, patch: str) -> str:
    """Format augment data as readable markdown."""
    lines = [f"# TFT Augments (Patch {patch})\n"]
    augments = data.get("data", {})
    for key, aug in sorted(augments.items(), key=lambda x: x[1].get("name", "")):
        name = aug.get("name", key)
        desc = aug.get("desc", "")
        tiers = aug.get("tier", [])
        tier_label = ", ".join(str(t) for t in tiers) if tiers else "?"

        lines.append(f"## {name} (Tier: {tier_label})")
        if desc:
            lines.append(f"Desc: {desc}")
        lines.append("")
    return "\n".join(lines)


def format_patch_data(data: TFTStaticData, patch: str) -> dict[str, tuple[str, dict]]:
    """Format all TFT static data into chunk-ready text with metadata.

    Returns dict: { "champions": (text, metadata), "traits": (text, metadata), ... }
    Only includes types that are present in the data dict.
    metadata = { "season": "SET17", "patch": "17.1", "type": "champions", ... }
    """
    season = _extract_season_from_patch(patch)

    chunks = {}
    for data_type, formatter in [
        ("champions", _format_champions),
        ("traits", _format_traits),
        ("items", _format_items),
        ("augments", _format_augments),
    ]:
        if data_type not in data:
            continue
        text = formatter(data[data_type], patch)
        metadata = {
            "season": season,
            "patch": patch,
            "type": data_type,
        }
        chunks[data_type] = (text, metadata)

    return chunks


async def ingest_tft_static(patch: str | None = None) -> dict[str, int | str]:
    """Download, cache, parse, embed, and ingest TFT static data into DB.

    Per-patch folder cache avoids re-downloading unchanged patch data (POLY-02).
    Hash-based deduplication avoids re-inserting unchanged chunks (RAG-05).

    Returns dict with:
      - patch: version string
      - status: "downloaded" | "cached"
      - ingested: number of chunks actually inserted
      - skipped: number of chunks skipped (hash match)
      - total: total chunks processed
    """
    # Determine latest version first to check cache status
    if patch is None:
        patch = await get_latest_version()

    was_cached = load_patch_from_cache(patch) is not None

    # Get patch data (cache-first, CDN fallback)
    version, data = await get_patch_data(patch)

    # Update global version marker
    cached_version = await get_cached_version()
    if version != cached_version:
        await save_cached_version(version)

    # Format into readable text chunks
    formatted_chunks = format_patch_data(data, version)

    # Build chunk list with hashes and metadata
    chunks_to_embed: list[dict] = []
    for data_type, (text, metadata) in formatted_chunks.items():
        chunks_to_embed.append({
            "type": data_type,
            "text": text,
            "hash": content_hash(text),
            "metadata": metadata,
        })

    if not chunks_to_embed:
        return {
            "patch": version,
            "status": "cached" if was_cached else "downloaded",
            "ingested": 0,
            "skipped": 0,
            "total": 0,
        }

    # Batch embed via Ollama
    texts = [c["text"] for c in chunks_to_embed]
    embeddings = await ollama.generate_embeddings(texts)

    # Insert into database with hash deduplication
    pool = await get_pool()
    stats = {"ingested": 0, "skipped": 0, "total": len(chunks_to_embed)}

    async with pool.acquire() as conn:
        for chunk, embedding in zip(chunks_to_embed, embeddings):
            source = f"tft_static:{chunk['type']}:{version}"

            # Check if already exists (hash dedup per D-09)
            existing = await conn.fetchval(
                "SELECT 1 FROM chunks WHERE source = $1 AND content_hash = $2",
                source,
                chunk["hash"],
            )
            if existing:
                stats["skipped"] += 1
                continue

            await conn.execute(
                """
                INSERT INTO chunks (content, content_hash, source, metadata, embedding)
                VALUES ($1, $2, $3, $4, $5::vector)
                ON CONFLICT (source, content_hash) DO NOTHING
                """,
                chunk["text"],
                chunk["hash"],
                source,
                chunk["metadata"],
                embedding,
            )
            stats["ingested"] += 1

    return {
        "patch": version,
        "status": "cached" if was_cached else "downloaded",
        **stats,
    }


if __name__ == "__main__":
    import sys

    patch_arg = sys.argv[1] if len(sys.argv) > 1 else None
    result = asyncio.run(ingest_tft_static(patch_arg))
    print(f"Patch {result['patch']}: {result['status']}, ingested={result['ingested']}, skipped={result['skipped']}, total={result['total']}")
