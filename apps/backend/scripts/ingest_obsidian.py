"""Ingest Obsidian vault markdown files into the knowledge base."""
from __future__ import annotations

import asyncio
from pathlib import Path

from app.db import get_pool
from app.services.ollama import ollama
from app.utils.markdown import extract_frontmatter, split_into_chunks
from app.utils.hashing import content_hash


BATCH_SIZE = 16  # VRAM-safe batch size for 16GB GPU


async def _split_with_heading(
    md_file: Path,
    body: str,
    chunk_size: int,
    overlap: int,
) -> list[tuple[str, dict]]:
    """Split markdown body into chunks with heading metadata."""
    heading_path = str(md_file)
    chunks = list(split_into_chunks(body, chunk_size=chunk_size, overlap=overlap))
    metadata = {"heading_path": heading_path, "source": str(md_file)}
    return [(chunk, metadata) for chunk in chunks]


async def ingest_vault(
    vault_path: str,
    chunk_size: int = 2000,
    overlap: int = 500,
) -> dict[str, int]:
    """Ingest all markdown files from an Obsidian vault.

    Args:
        vault_path: Path to the Obsidian vault directory.
        chunk_size: Target chunk size in characters (default 2000).
        overlap: Overlap between chunks in characters (default 500).

    Returns:
        dict with keys: files (files processed), chunks (total chunks inserted),
        skipped (files unchanged).
    """
    vault = Path(vault_path)
    if not vault.exists():
        raise FileNotFoundError(f"Vault not found: {vault_path}")

    pool = await get_pool()
    stats: dict[str, int] = {"files": 0, "chunks": 0, "skipped": 0}

    async with pool.acquire() as conn:
        for md_file in vault.rglob("*.md"):
            # Skip .obsidian directory
            if ".obsidian" in md_file.parts:
                continue

            file_text = md_file.read_text(encoding="utf-8")
            file_hash = content_hash(file_text)

            # Check if file changed
            existing = await conn.fetchval(
                "SELECT 1 FROM chunks WHERE source = $1 AND content_hash = $2",
                str(md_file),
                file_hash,
            )
            if existing:
                stats["skipped"] += 1
                continue

            # Parse and split
            fm, body = extract_frontmatter(file_text)
            chunks_with_meta = await _split_with_heading(md_file, body, chunk_size, overlap)

            # Batch embed and insert
            texts = [chunk for chunk, _ in chunks_with_meta]
            if texts:
                embeddings = await ollama.generate_embeddings(texts)

                for (chunk_text, meta), embedding in zip(chunks_with_meta, embeddings):
                    chunk_hash = content_hash(chunk_text)
                    await conn.execute(
                        """
                        INSERT INTO chunks (content, content_hash, source, metadata, embedding)
                        VALUES ($1, $2, $3, $4, $5::vector)
                        ON CONFLICT (source, content_hash) DO NOTHING
                        """,
                        chunk_text,
                        chunk_hash,
                        str(md_file),
                        meta,
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
