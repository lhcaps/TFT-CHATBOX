"""Ingest Obsidian vault markdown files into the knowledge base."""
from __future__ import annotations

import asyncio
from pathlib import Path

from app.db import get_pool
from app.services.ollama import ollama
from app.utils.markdown import extract_frontmatter, split_into_chunks
from app.utils.hashing import content_hash


async def ingest_vault(vault_path: str, chunk_size: int = 512) -> dict[str, int]:
    """Ingest all markdown files from an Obsidian vault."""
    vault = Path(vault_path)
    if not vault.exists():
        raise FileNotFoundError(f"Vault not found: {vault_path}")

    pool = await get_pool()
    stats = {"files": 0, "chunks": 0, "skipped": 0}

    async with pool.acquire() as conn:
        for md_file in vault.rglob("*.md"):
            file_hash = content_hash(md_file.read_text(encoding="utf-8"))
            existing = await conn.fetchval(
                "SELECT 1 FROM chunks WHERE source = $1 AND content_hash = $2",
                str(md_file),
                file_hash,
            )
            if existing:
                stats["skipped"] += 1
                continue

            text = md_file.read_text(encoding="utf-8")
            fm, body = extract_frontmatter(text)
            chunks = list(split_into_chunks(body, chunk_size))

            for chunk_text in chunks:
                embedding = await ollama.generate_embedding(chunk_text)
                await conn.execute(
                    """
                    INSERT INTO chunks (content, content_hash, source, metadata, embedding)
                    VALUES ($1, $2, $3, $4, $5::vector)
                    """,
                    chunk_text,
                    content_hash(chunk_text),
                    str(md_file),
                    fm,
                    embedding,
                )
                stats["chunks"] += 1

            stats["files"] += 1

    return stats


if __name__ == "__main__":
    import sys
    vault_path = sys.argv[1] if len(sys.argv) > 1 else "."
    result = asyncio.run(ingest_vault(vault_path))
    print(f"Ingested {result['files']} files, {result['chunks']} chunks, {result['skipped']} skipped")
