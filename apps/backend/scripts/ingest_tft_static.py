"""Ingest TFT static data (champions, traits, items, augments) into the knowledge base."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.db import get_pool
from app.services.ollama import ollama
from app.utils.hashing import content_hash


TFT_STATIC_FILES = {
    "champions": "tft-static-schema.json",
    "traits": "tft-traits-schema.json",
    "items": "tft-items-schema.json",
    "augments": "tft-augments-schema.json",
}


async def ingest_tft_static(data_dir: str = ".") -> dict[str, int]:
    """Ingest TFT static JSON files into the knowledge base."""
    pool = await get_pool()
    stats = {"types": 0, "chunks": 0}

    async with pool.acquire() as conn:
        for data_type, filename in TFT_STATIC_FILES.items():
            filepath = Path(data_dir) / filename
            if not filepath.exists():
                continue

            content = filepath.read_text(encoding="utf-8")
            data = json.loads(content)
            text = _format_static_data(data_type, data)
            chunk_hash = content_hash(text)

            existing = await conn.fetchval(
                "SELECT 1 FROM chunks WHERE source = $1 AND content_hash = $2",
                f"tft_static:{data_type}",
                chunk_hash,
            )
            if existing:
                continue

            embedding = await ollama.generate_embedding(text)
            await conn.execute(
                """
                INSERT INTO chunks (content, content_hash, source, metadata, embedding)
                VALUES ($1, $2, $3, $4, $5::vector)
                ON CONFLICT (source, content_hash) DO NOTHING
                """,
                text,
                chunk_hash,
                f"tft_static:{data_type}",
                {"type": data_type},
                embedding,
            )
            stats["chunks"] += 1
            stats["types"] += 1

    return stats


def _format_static_data(data_type: str, data: dict) -> str:
    """Format static data as readable text for embedding."""
    lines = [f"# TFT {data_type.capitalize()}\n"]
    if isinstance(data, dict):
        for key, value in data.items():
            lines.append(f"## {key}: {value}")
    elif isinstance(data, list):
        for item in data:
            lines.append(f"- {item}")
    return "\n".join(lines)


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    import sys
    result = asyncio.run(ingest_tft_static(data_dir))
    print(f"Ingested {result['types']} types, {result['chunks']} chunks")
