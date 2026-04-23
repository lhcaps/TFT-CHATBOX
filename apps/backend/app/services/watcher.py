"""File system watcher for Obsidian vault reactive sync (RAG2-05)."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object
    FileSystemEvent = None

from app.config import settings

logger = logging.getLogger(__name__)


class ObsidianFileHandler(FileSystemEventHandler):
    """Handles file system events from watchdog."""

    def __init__(self, watcher: "FileSystemWatcher | None" = None):
        self.watcher = watcher
        self._debounce_seconds = 0.5  # 500ms debounce (RAG2-05)

    def on_modified(self, event: FileSystemEvent | None):
        if event is None or event.is_directory:
            return
        self._schedule_debounced(event)

    def on_created(self, event: FileSystemEvent | None):
        if event is None or event.is_directory:
            return
        self._schedule_debounced(event)

    def on_deleted(self, event: FileSystemEvent | None):
        if event is None or event.is_directory:
            return
        self._schedule_debounced(event)

    def _schedule_debounced(self, event: FileSystemEvent | None):
        if event is None:
            return
        file_path = event.src_path

        # Skip non-markdown files
        if not file_path.endswith(('.md', '.markdown')):
            return

        if self.watcher is None:
            return

        # Schedule debounced trigger in a background thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def delayed_trigger():
            await asyncio.sleep(self._debounce_seconds)
            await self.watcher.trigger_reactive_ingest(file_path, getattr(event, 'event_type', 'modified'))

        def run_async():
            loop.run_until_complete(delayed_trigger())

        timer = threading.Timer(self._debounce_seconds, run_async)
        timer.start()


class FileSystemWatcher:
    """Manages file system watching for Obsidian vault.

    Watches vault directory for .md file changes and triggers
    reactive re-ingest after 500ms debounce (RAG2-05).
    """

    _instance: "FileSystemWatcher | None" = None

    def __init__(self):
        self.observer: Any = None
        self.handler: ObsidianFileHandler | None = None
        self.vault_path: str = ""
        self.is_watching: bool = False
        self.started_at: str | None = None
        self.event_log: list[dict[str, Any]] = []
        self.file_hashes: dict[str, str] = {}  # path -> content hash

    @classmethod
    def get_instance(cls) -> "FileSystemWatcher":
        if cls._instance is None:
            cls._instance = FileSystemWatcher()
        return cls._instance

    def start(self, vault_path: str) -> dict[str, Any]:
        """Start watching the vault directory."""
        if not WATCHDOG_AVAILABLE:
            raise ImportError(
                "watchdog is not installed. Run: pip install watchdog>=4.0.0"
            )

        if self.is_watching:
            return {
                "watching": True,
                "vault_path": self.vault_path,
                "message": "Already watching",
                "started_at": self.started_at,
            }

        vault = Path(vault_path)
        if not vault.exists():
            raise FileNotFoundError(f"Vault path not found: {vault_path}")

        self.vault_path = vault_path
        self.handler = ObsidianFileHandler(self)
        self.observer = Observer()
        self.observer.schedule(self.handler, str(vault), recursive=True)
        self.observer.start()
        self.is_watching = True
        self.started_at = datetime.now(timezone.utc).isoformat()

        md_files = list(vault.rglob("*.md"))
        logger.info(f"Started watching vault: {vault_path} ({len(md_files)} .md files)")

        return {
            "watching": True,
            "vault_path": vault_path,
            "files": len(md_files),
            "started_at": self.started_at,
        }

    def stop(self) -> dict[str, Any]:
        """Stop watching the vault directory."""
        if not self.is_watching:
            return {"watching": False}

        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.observer = None

        self.is_watching = False
        self.handler = None
        logger.info("Stopped watching vault")

        return {"watching": False}

    def get_status(self) -> dict[str, Any]:
        """Get watcher status."""
        return {
            "watching": self.is_watching,
            "vault_path": self.vault_path if self.is_watching else None,
            "started_at": self.started_at,
            "events_count": len(self.event_log),
            "last_event": self.event_log[-1] if self.event_log else None,
        }

    async def trigger_reactive_ingest(self, file_path: str, event_type: str):
        """Trigger reactive ingest for a changed file."""
        logger.info(f"Reactive ingest triggered: {event_type} {file_path}")

        event_record: dict[str, Any] = {
            "event": event_type,
            "path": file_path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "pending",
        }
        self.event_log.append(event_record)

        try:
            path = Path(file_path)
            if path.exists() and event_type != "deleted":
                content = path.read_text(encoding="utf-8")

                content_hash = hashlib.md5(content.encode()).hexdigest()

                if file_path in self.file_hashes and self.file_hashes[file_path] == content_hash:
                    logger.debug(f"Skipping {file_path}: hash unchanged")
                    event_record["action"] = "skipped_hash_unchanged"
                    return

                self.file_hashes[file_path] = content_hash
                await self._reingest_file(file_path, content)
                event_record["action"] = "re-ingested"
            else:
                if file_path in self.file_hashes:
                    del self.file_hashes[file_path]
                event_record["action"] = "deleted_file_removed_from_cache"

            logger.info(f"Reactive ingest complete: {event_type} {file_path}")

        except Exception as e:
            logger.exception(f"Reactive ingest failed for {file_path}")
            event_record["action"] = f"error: {str(e)[:100]}"

    async def _reingest_file(self, file_path: str, content: str):
        """Re-embed and upsert a single file to the vector DB."""
        from app.db import get_pool
        from app.services.ollama import ollama

        pool = await get_pool()

        chunks = self._chunk_content(content, settings.rag_chunk_size)

        for i, chunk_text in enumerate(chunks):
            raw_embedding = await ollama.generate_embedding(chunk_text)
            embedding = raw_embedding[: settings.ollama_embedding_dims]
            source = f"obsidian:{file_path}"

            async with pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM document_chunks WHERE source = $1 AND metadata->>'source_file' = $2",
                    source,
                    file_path,
                )

                metadata = {
                    "entity_type": "general",
                    "source_file": file_path,
                    "chunk_index": i,
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                    "patch": "17.1",
                }

                await conn.execute(
                    """
                    INSERT INTO document_chunks (content, embedding, source, metadata)
                    VALUES ($1, $2::vector, $3, $4)
                    """,
                    chunk_text,
                    json.dumps(embedding),
                    source,
                    json.dumps(metadata),
                )

        logger.info(f"Re-ingested {len(chunks)} chunks from {file_path}")

    @staticmethod
    def _chunk_content(content: str, chunk_size: int) -> list[str]:
        """Split content into chunks by paragraphs."""
        paragraphs = content.split("\n\n")
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if current_size + len(para) > chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_size = len(para)
            else:
                current_chunk.append(para)
                current_size += len(para)

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks if chunks else [content[:chunk_size]]
