"""Base processor class for modular TFT data ingestion (RAG2-04)."""
from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.config import settings
from app.db import get_pool
from app.services.ollama import ollama

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Base class for all data processors.

    Subclasses override source_file, entity_type, chunk_size, and process_item().
    """

    source_file: str = ""       # JSON filename in project root
    entity_type: str = ""       # entity_type metadata value
    chunk_size: int = 300        # target chars per chunk

    def __init__(self) -> None:
        self.ingested_count = 0
        self.skipped_count = 0
        self.seen_hashes: set[str] = set()

    @abstractmethod
    def process_item(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        """Convert a single data item into chunk(s).

        Returns list of chunk dicts with: content, metadata
        """
        raise NotImplementedError

    def get_data_path(self) -> Path:
        """Get path to data file in project root.

        Project root is 2 levels up from scripts/ingest/
        """
        backend_dir = Path(__file__).parent.parent.parent.parent
        return backend_dir / self.source_file

    def load_data(self) -> list[dict[str, Any]]:
        """Load JSON data from source file."""
        data_path = self.get_data_path()
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute content hash for deduplication."""
        return hashlib.md5(content.encode()).hexdigest()

    async def ingest(self) -> dict[str, Any]:
        """Main ingest method — loads data, processes items, upserts chunks."""
        logger.info(f"Starting {self.__class__.__name__} ingest...")
        data = self.load_data()
        all_chunks: list[dict[str, Any]] = []

        for item in data:
            try:
                chunks = self.process_item(item)
                for chunk in chunks:
                    content_hash = self.compute_hash(chunk["content"])
                    if content_hash in self.seen_hashes:
                        self.skipped_count += 1
                        continue
                    self.seen_hashes.add(content_hash)
                    all_chunks.append(chunk)
            except Exception as e:
                logger.warning(f"Failed to process item: {e}")
                self.skipped_count += 1

        if all_chunks:
            await self._upsert_chunks(all_chunks)

        logger.info(
            f"{self.__class__.__name__}: ingested={self.ingested_count}, "
            f"skipped={self.skipped_count}, total={len(all_chunks)}"
        )
        return {
            "processor": self.__class__.__name__,
            "ingested": self.ingested_count,
            "skipped": self.skipped_count,
            "total_chunks": len(all_chunks),
        }

    async def _upsert_chunks(self, chunks: list[dict[str, Any]]) -> None:
        """Generate embeddings and upsert chunks to database."""
        pool = await get_pool()

        for chunk in chunks:
            raw_embedding = await ollama.generate_embedding(chunk["content"])
            embedding = raw_embedding[: settings.ollama_embedding_dims]

            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO document_chunks (content, embedding, source, metadata)
                    VALUES ($1, $2::vector, $3, $4)
                    ON CONFLICT DO NOTHING
                    """,
                    chunk["content"],
                    json.dumps(embedding),
                    chunk.get("source", self.source_file),
                    json.dumps(chunk.get("metadata", {})),
                )
            self.ingested_count += 1
