"""Ingest TFT Set 17 / Patch 17.1 clean data pack into the RAG chunks table.

Loads tft_set17_patch17_1_data_pack.json and converts each section into
Markdown chunks with embeddings, then upserts into the chunks table with
source='tft_set17'.

Usage:
    python scripts/ingest_tft_set17.py              # full ingest
    python scripts/ingest_tft_set17.py --section systems  # single section
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_pool
from app.services.ollama import ollama


DATA_PACK_PATH = Path(__file__).parent.parent.parent.parent / "tft_set17_patch17_1_data_pack.json"
MAX_EMBEDDING_DIMS = 1024


# ─── Markdown chunk builders ───────────────────────────────────────────────────

def chunk_systems(meta: dict, systems: dict) -> list[dict]:
    chunks = []

    # Realm of the Gods
    rotg = systems.get("realm_of_the_gods", {})
    lines = ["# Realm of the Gods", ""]
    for step in rotg.get("flow", []):
        lines.append(f"- {step}")
    lines.append("")
    lines.append("*Set 17 core mechanic — replaces Carousel*")
    chunks.append({
        "title": "Realm of the Gods",
        "content": "\n".join(lines),
        "tags": ["set17", "mechanic", "system"],
    })

    # 9 Gods
    gods = systems.get("space_gods", [])
    god_lines = ["# 9 Space Gods — Set 17", ""]
    for g in gods:
        god_lines.append(f"## {g['name']} ({g['title']})")
        god_lines.append(f"**Focus:** {g['focus']}")
        god_lines.append("")
    god_lines.append("*Choose your god wisely — each grants unique boons throughout the game*")
    chunks.append({
        "title": "9 Space Gods Overview",
        "content": "\n".join(god_lines),
        "tags": ["set17", "god", "mechanic"],
    })

    # Patch 17.1B changes
    p17b = systems.get("patch_17_1b_highlights", {})
    lines = ["# Patch 17.1B Changes", ""]
    augs = p17b.get("augments_removed", [])
    if augs:
        lines.append("## Augments Removed")
        for a in augs:
            lines.append(f"- ~~{a}~~")
        lines.append("")
    for tc in p17b.get("traits_changed", []):
        lines.append(f"## Trait: {tc['name']}")
        lines.append(f"- {tc['change']}")
        lines.append("")
    for sc in p17b.get("system_changes", []):
        name = sc.get("name", "")
        change = sc.get("change", "") or sc.get("to", "")
        lines.append(f"## {name}")
        if sc.get("from"):
            lines.append(f"- ~~{sc['from']}~~ → {sc['to']}")
        else:
            lines.append(f"- {change}")
        lines.append("")
    kw = p17b.get("keyword_changes", [])
    if kw:
        lines.append("## Keyword Renames")
        for k in kw:
            lines.append(f"- ~~{k['from']}~~ → **{k['to']}**")
        lines.append("")
    lines.append("*Source: Riot Games — patch 17.1B*")
    chunks.append({
        "title": "Patch 17.1B Changes",
        "content": "\n".join(lines),
        "tags": ["set17", "patch", "balance"],
    })

    return chunks


def chunk_origins(origins: list[dict]) -> list[dict]:
    chunks = []
    for origin in origins:
        name = origin["name"]
        champions = origin.get("champions", [])
        breakpoints = origin.get("breakpoints", [])
        summary = origin.get("summary", "")

        lines = [f"# Origin: {name}", ""]
        lines.append(f"**Breakpoints:** {', '.join(str(b) for b in breakpoints)}")
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append("**Champions:** " + ", ".join(champions))
        lines.append("")
        lines.append(f"*Set 17 Space Gods*")
        chunks.append({
            "title": f"Origin: {name}",
            "content": "\n".join(lines),
            "tags": ["set17", "origin", "trait"],
        })

    return chunks


def chunk_classes(classes: list[dict]) -> list[dict]:
    chunks = []
    for cls in classes:
        name = cls["name"]
        champions = cls.get("champions", [])
        breakpoints = cls.get("breakpoints", [])
        summary = cls.get("summary", "")

        lines = [f"# Class: {name}", ""]
        lines.append(f"**Breakpoints:** {', '.join(str(b) for b in breakpoints)}")
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append("**Champions:** " + ", ".join(champions))
        lines.append("")
        lines.append(f"*Set 17 Space Gods*")
        chunks.append({
            "title": f"Class: {name}",
            "content": "\n".join(lines),
            "tags": ["set17", "class", "trait"],
        })

    return chunks


def chunk_champions(champions: list[dict]) -> list[dict]:
    chunks = []
    for champ in champions:
        name = champ["name"]
        cost = champ["cost"]
        traits = champ.get("traits", [])
        stars = "⭐" * cost
        lines = [f"# Champion: {name}", ""]
        lines.append(f"**Cost:** {cost} ({stars})")
        lines.append(f"**Traits:** {', '.join(traits)}")
        if champ.get("summary"):
            lines.append("")
            lines.append(champ["summary"])
        lines.append("")
        lines.append(f"*Set 17 Space Gods | Patch 17.1*")
        chunks.append({
            "title": f"Champion: {name}",
            "content": "\n".join(lines),
            "tags": ["set17", "champion", f"cost{cost}"],
        })

    # Also group by cost tier
    by_cost: dict[int, list[dict]] = {}
    for c in champions:
        by_cost.setdefault(c["cost"], []).append(c["name"])

    for cost, names in sorted(by_cost.items()):
        stars = "⭐" * cost
        lines = [f"# {cost}-Cost Champions — Set 17", ""]
        lines.append(f"**Tier:** {stars} ({cost}⭐)")
        lines.append("")
        lines.append(", ".join(names))
        lines.append("")
        lines.append(f"*Patch 17.1*")
        chunks.append({
            "title": f"{cost}-Cost Champions",
            "content": "\n".join(lines),
            "tags": ["set17", "champion", f"cost{cost}"],
        })

    return chunks


def chunk_items(items: dict) -> list[dict]:
    chunks = []
    for category, item_list in items.items():
        if not isinstance(item_list, list):
            continue
        cat_name = category.replace("_", " ").title()
        lines = [f"# Items: {cat_name}", ""]
        for item in item_list:
            if isinstance(item, dict):
                name = item.get("name", item.get("title", "Unknown"))
                desc = item.get("description", item.get("desc", ""))
                lines.append(f"## {name}")
                if desc:
                    lines.append(desc)
                lines.append("")
            else:
                lines.append(f"- {item}")
        lines.append(f"*Set 17 Space Gods*")
        chunks.append({
            "title": f"Items: {cat_name}",
            "content": "\n".join(lines),
            "tags": ["set17", "items", category],
        })
    return chunks


def chunk_meta_comps(meta_comps: dict) -> list[dict]:
    chunks = []

    # S-tier
    s_tier = meta_comps.get("s_tier_snapshot_17_1", [])
    lines = ["# S-Tier Comps — Patch 17.1 Meta Snapshot", ""]
    lines.append("*Source: Mobalytics + Riot patch data — verified snapshot*")
    lines.append("")
    for i, comp in enumerate(s_tier, 1):
        carries = ", ".join(comp.get("carries", []))
        leveling = comp.get("leveling", "N/A")
        notes = comp.get("notes", [])
        lines.append(f"## {i}. {comp['name']}")
        lines.append(f"**Carries:** {carries}")
        lines.append(f"**Leveling:** {leveling}")
        if notes:
            for n in notes:
                lines.append(f"- {n}")
        lines.append("")
    lines.append("*Meta shifts daily — re-ingest via /api/ingest/metatft for fresh data*")
    chunks.append({
        "title": "S-Tier Meta Comps — Patch 17.1",
        "content": "\n".join(lines),
        "tags": ["set17", "meta", "s-tier", "patch17.1"],
    })

    # A-tier
    a_tier = meta_comps.get("a_tier_snapshot_17_1", [])
    lines = ["# A-Tier Comps — Patch 17.1 Meta Snapshot", ""]
    for comp in a_tier:
        lines.append(f"- {comp}")
    lines.append("")
    lines.append("*Meta shifts daily — re-ingest via /api/ingest/metatft for fresh data*")
    chunks.append({
        "title": "A-Tier Meta Comps — Patch 17.1",
        "content": "\n".join(lines),
        "tags": ["set17", "meta", "a-tier", "patch17.1"],
    })

    # Full meta comp cards
    for comp in s_tier:
        carries = comp.get("carries", [])
        leveling = comp.get("leveling", "")
        lines = [f"# Comp: {comp['name']}", ""]
        lines.append(f"**Leveling:** {leveling}")
        lines.append("")
        lines.append(f"**Carries:** {', '.join(carries)}")
        lines.append("")
        lines.append(f"*Nguon: Mobalytics/SpaceGods | Patch: 17.1*")
        chunks.append({
            "title": f"Meta: {comp['name']}",
            "content": "\n".join(lines),
            "tags": ["set17", "meta", "comp", comp["name"].lower().replace(" ", "-")],
        })

    return chunks


# ─── Core ingestion ────────────────────────────────────────────────────────────

async def generate_embedding(text: str) -> list[float]:
    """Generate embedding using Ollama single-embed endpoint."""
    try:
        embedding = await ollama.generate_embedding(text)
        if len(embedding) < MAX_EMBEDDING_DIMS:
            embedding += [0.0] * (MAX_EMBEDDING_DIMS - len(embedding))
        elif len(embedding) > MAX_EMBEDDING_DIMS:
            embedding = embedding[:MAX_EMBEDDING_DIMS]
        return embedding
    except Exception:
        return [0.0] * MAX_EMBEDDING_DIMS


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


async def upsert_chunk(
    pool,
    chunk: dict,
    source: str,
    patch: str = "17.1",
) -> bool:
    """Insert or skip one chunk. Returns True if inserted, False if skipped."""
    content = chunk["content"]
    chash = content_hash(content)
    tags = chunk.get("tags", [])
    title = chunk.get("title", "")
    meta = {"title": title, "patch": patch, "tags": tags}

    async with pool.acquire() as conn:
        # Build embedding as '[v1,v2,...]' string, cast to vector in SQL
        emb = await generate_embedding(content)
        emb_str = "[" + ",".join(str(v) for v in emb) + "]"
        row = await conn.fetchrow(
            """
            INSERT INTO chunks (content, content_hash, source, metadata, embedding)
            VALUES ($1, $2, $3, $4, $5::vector)
            ON CONFLICT (source, content_hash) DO UPDATE
                SET metadata = EXCLUDED.metadata
            """,
            content,
            chash,
            source,
            json.dumps(meta),
            emb_str,
        )
        # Check if row was actually inserted
        row2 = await conn.fetchrow(
            "SELECT 1 FROM chunks WHERE source = $1 AND content_hash = $2",
            source,
            chash,
        )
        return row2 is not None


async def ingest_all() -> dict:
    """Load the data pack and ingest all sections."""
    print(f"Loading data pack from: {DATA_PACK_PATH}")
    if not DATA_PACK_PATH.exists():
        raise FileNotFoundError(f"Data pack not found: {DATA_PACK_PATH}")

    with open(DATA_PACK_PATH, "r", encoding="utf-8") as f:
        pack = json.load(f)

    meta = pack.get("metadata", {})
    systems = pack.get("systems", {})
    origins = pack.get("origins", [])
    classes_ = pack.get("classes", [])
    champions = pack.get("champions", [])
    items = pack.get("items", {})
    meta_comps = pack.get("meta_comps", {})

    pool = await get_pool()

    all_chunks: list[dict] = []
    all_chunks += chunk_systems(meta, systems)
    all_chunks += chunk_origins(origins)
    all_chunks += chunk_classes(classes_)
    all_chunks += chunk_champions(champions)
    all_chunks += chunk_items(items)
    all_chunks += chunk_meta_comps(meta_comps)

    print(f"Total chunks to ingest: {len(all_chunks)}")

    total_inserted = 0
    total_skipped = 0

    for i, chunk in enumerate(all_chunks, 1):
        inserted = await upsert_chunk(pool, chunk, source="tft_set17", patch="17.1")
        if inserted:
            total_inserted += 1
        else:
            total_skipped += 1
        if i % 20 == 0:
            print(f"  [{i}/{len(all_chunks)}] {total_inserted} inserted, {total_skipped} skipped")

    print(f"\nDone! {total_inserted} inserted, {total_skipped} skipped (already existed)")

    return {
        "total_chunks": len(all_chunks),
        "inserted": total_inserted,
        "skipped": total_skipped,
        "source": "tft_set17",
        "patch": "17.1",
    }


# ─── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = asyncio.run(ingest_all())
    print(json.dumps(result, indent=2))
