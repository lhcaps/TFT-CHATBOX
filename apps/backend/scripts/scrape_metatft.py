"""Scrape TFT comps from MetaTFT and ingest into DB using httpx + regex.

D-01: NO browser automation. httpx + regex only.
D-02: Data source: https://www.metatft.com/comps
D-03: Transform to Vietnamese Markdown chunks.
D-04: source='metatft' tag, dedup by source+content_hash.
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Optional

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_pool
from app.services.ollama import ollama
from app.utils.hashing import content_hash

METATFT_COMPS_URL = "https://www.metatft.com/comps"
MAX_EMBEDDING_DIMS = 1024

# ─── Fetch & Parse ──────────────────────────────────────────────────────────

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


def extract_json_from_html(html: str) -> dict | None:
    """Extract embedded JSON from metatft.com page using regex patterns.

    MetaTFT embeds data in window.__INITIAL_STATE__ or similar.
    Returns the parsed dict or None if extraction fails.
    """
    # Try window.__INITIAL_STATE__ first (most common pattern)
    patterns = [
        r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;?\s*$',
        r'"comps":\s*(\[.*?\])\s*,\s*"units"',
        r'window\.__NUXT__\s*=\s*(\{.*?\})\s*;?\s*$',
    ]
    for pattern in patterns:
        m = re.search(pattern, html, re.DOTALL | re.MULTILINE)
        if m:
            raw = m.group(1)
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                # Try to find and fix the JSON boundary
                pass

    # Fallback: find any large JSON object in the page
    # Look for comps data array with champion names
    m = re.search(r'"comps"\s*:\s*(\[[\s\S]{100,}?\])\s*,\s*"units"', html)
    if m:
        try:
            return {"comps": json.loads(m.group(1))}
        except json.JSONDecodeError:
            pass

    # Last resort: try extracting a self-contained JSON block
    m = re.search(r'(\{[\s\S]*?"comps"[\s\S]*?\})\s*[,\n]', html)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    return None


def parse_comps_data(data: dict) -> list[dict]:
    """Parse comps from extracted JSON data.

    MetaTFT JSON structure varies. Try multiple extraction paths.
    Returns list of comp dicts with: name, tier, top4_rate, avg_place, carry, items, units, traits.
    """
    comps = []

    # Path 1: data.comps (direct array)
    raw_comps = data.get("comps") or data.get("data") or data.get("units") or []
    if not isinstance(raw_comps, list):
        # Try to find the comps array somewhere in the data
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                first = value[0]
                if isinstance(first, dict) and any(
                    k in first for k in ("name", "champions", "units", "items", "tier")
                ):
                    raw_comps = value
                    break

    for entry in raw_comps:
        if not isinstance(entry, dict):
            continue

        # Extract tier from placement keys or tier field
        tier = entry.get("tier") or entry.get("placement") or "B"
        top4 = entry.get("top4") or entry.get("top4_rate") or entry.get("winrate") or "0"
        avg_place = entry.get("avg_place") or entry.get("average") or "5.0"
        units = entry.get("units") or entry.get("champions") or entry.get("units_list") or []
        items = entry.get("items") or entry.get("core_items") or []

        # Get comp name — may be nested
        name = (
            entry.get("name")
            or entry.get("comp_name")
            or entry.get("title")
            or entry.get("comp", {})
            if isinstance(entry.get("comp"), dict)
            else entry.get("comp", "")
        )
        if not name:
            # Try champion-based naming
            if units and len(units) > 0:
                first_unit = units[0] if isinstance(units[0], str) else units[0].get("name", "Unknown")
                name = f"{first_unit} Board"
            else:
                name = "Unknown Comp"

        # Normalize tier
        tier_str = str(tier).upper()
        if "S" in tier_str:
            tier_norm = "S"
        elif "A" in tier_str:
            tier_norm = "A"
        else:
            tier_norm = "B"

        # Normalize units to list of strings
        if isinstance(units, dict):
            units = list(units.values()) if units else []
        unit_names = []
        for u in units:
            if isinstance(u, str):
                unit_names.append(u)
            elif isinstance(u, dict):
                n = u.get("name") or u.get("champion") or u.get("unit", "Unknown")
                unit_names.append(n)

        # Normalize items
        if isinstance(items, dict):
            items = list(items.values()) if items else []
        item_names = []
        for it in items:
            if isinstance(it, str):
                item_names.append(it)
            elif isinstance(it, dict):
                n = it.get("name") or it.get("item", "Unknown Item")
                item_names.append(n)

        # Extract carry (first or designated)
        carry_name = entry.get("carry") or entry.get("primary_carry") or (
            unit_names[0] if unit_names else "Unknown"
        )

        # Traits
        traits_raw = entry.get("traits") or entry.get("trait_list") or []
        if isinstance(traits_raw, dict):
            traits_raw = [
                {"name": k, "count": v} for k, v in traits_raw.items()
            ]
        traits_list = []
        for t in traits_raw:
            if isinstance(t, str):
                traits_list.append({"name": t, "count": 1})
            elif isinstance(t, dict):
                traits_list.append({
                    "name": t.get("name") or t.get("trait", "Unknown"),
                    "count": t.get("count") or t.get("num") or 1,
                })

        comps.append({
            "name": str(name),
            "tier": tier_norm,
            "top4_rate": str(top4).replace("%", ""),
            "avg_place": str(avg_place),
            "carry": str(carry_name),
            "items": item_names,
            "units": unit_names,
            "traits": traits_list,
        })

    return comps


def extract_comps_from_html(html: str) -> list[dict]:
    """Main entry point: fetch page and extract comps."""
    data = extract_json_from_html(html)
    if data is None:
        return []
    return parse_comps_data(data)


# ─── Transform to Vietnamese Markdown ──────────────────────────────────────────

def comp_to_markdown(comp: dict, patch_version: str = "latest") -> str:
    """Transform a comp dict to Vietnamese Markdown.

    Format: "Theo MetaTFT hien tai, Dong hinh [Ten] dang o Tier [S/A/B] voi [X]% ti le Top 4..."
    """
    tier = comp.get("tier", "B")
    name = comp.get("name", "Unknown")
    top4 = comp.get("top4_rate", "0")
    avg = comp.get("avg_place", "5.0")
    carry = comp.get("carry", "Unknown")
    items = comp.get("items", [])
    units = comp.get("units", [])
    traits = comp.get("traits", [])

    items_str = " ".join(f"[{it}]" for it in items)
    units_str = ", ".join(units)
    traits_str = ", ".join([
        f"{t['name']} {t['count']}" for t in traits
    ])

    lines = [
        f"# Comp: {name}",
        "",
        f"**Tier:** {tier} | **Top4:** {top4}% | **Avg Place:** {avg}",
        "",
        f"**Carry:** {carry}",
        "",
        f"**Items:** {items_str}",
        "",
        f"**Units:** {units_str}",
        "",
        f"**Traits:** {traits_str}",
        "",
        f"*Nguon: MetaTFT | Patch: {patch_version}*",
    ]
    return "\n".join(lines)


# ─── Database Ingestion ─────────────────────────────────────────────────────

async def ingest_into_db(comps: list[dict], patch_version: str) -> dict:
    """Insert comp chunks into DB with embeddings."""
    if not comps:
        return {"ingested": 0, "skipped": 0, "total": 0}

    texts = []
    sources = []
    for comp in comps:
        md = comp_to_markdown(comp, patch_version)
        slug = re.sub(r"[^a-z0-9]+", "_", comp["name"].lower())[:50]
        texts.append(md)
        sources.append(f"metatft:comps:{slug}")

    raw_embeddings = await ollama.generate_embeddings(texts)
    embeddings = [emb[:MAX_EMBEDDING_DIMS] for emb in raw_embeddings]

    hashes = [content_hash(t) for t in texts]

    pool = await get_pool()
    stats = {"ingested": 0, "skipped": 0, "total": len(comps)}

    async with pool.acquire() as conn:
        for text, source, embedding, hash_ in zip(texts, sources, embeddings, hashes):
            existing = await conn.fetchval(
                "SELECT 1 FROM chunks WHERE source = $1 AND content_hash = $2",
                source,
                hash_,
            )
            if existing:
                stats["skipped"] += 1
                continue

            embedding_str = json.dumps(embedding)
            metadata = {
                "season": "SET17",
                "patch": patch_version,
                "type": "metatft_comps",
                "source": "metatft",
            }
            await conn.execute(
                """
                INSERT INTO chunks (content, content_hash, source, metadata, embedding)
                VALUES ($1, $2, $3, $4::jsonb, $5::vector)
                ON CONFLICT (source, content_hash) DO NOTHING
                """,
                text,
                hash_,
                source,
                json.dumps(metadata),
                embedding_str,
            )
            stats["ingested"] += 1

    return stats


# ─── Public API ────────────────────────────────────────────────────────────

async def scrape_and_ingest(patch: Optional[str] = None) -> dict:
    """Scrape MetaTFT comps and ingest into DB.

    If patch is None, uses 'latest'.
    Returns dict with ingested/skipped/total counts.
    """
    html = fetch_page(METATFT_COMPS_URL)
    comps = extract_comps_from_html(html)

    patch_version = patch or "latest"
    stats = await ingest_into_db(comps, patch_version)
    stats["patch"] = patch_version
    stats["comps_count"] = len(comps)
    return stats


# ─── CLI Entry Point ──────────────────────────────────────────────────────

async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Scrape MetaTFT comps and ingest into DB")
    parser.add_argument(
        "patch",
        nargs="?",
        default=None,
        help="Patch version (e.g. 17.1). Defaults to 'latest'.",
    )
    args = parser.parse_args()

    print(f"Scraping MetaTFT comps from {METATFT_COMPS_URL}...")
    stats = await scrape_and_ingest(args.patch)
    print(
        f"Done! patch={stats['patch']}, "
        f"comps={stats['comps_count']}, "
        f"ingested={stats['ingested']}, "
        f"skipped={stats['skipped']}, "
        f"total={stats['total']}"
    )


if __name__ == "__main__":
    asyncio.run(main())
