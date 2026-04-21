"""Session repository for database persistence."""
from __future__ import annotations

import uuid
from typing import Optional

import asyncpg


class SessionRepository:
    """Repository for session CRUD operations."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def create(self, title: Optional[str], mode: str) -> dict:
        """Create a new session."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO sessions (id, title, mode)
                VALUES ($1, $2, $3)
                RETURNING id, title, mode, created_at, updated_at
                """,
                uuid.uuid4().hex[:8],
                title,
                mode,
            )
            return dict(row)

    async def get(self, session_id: str) -> Optional[dict]:
        """Get a session by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, title, mode, created_at, updated_at FROM sessions WHERE id = $1",
                session_id,
            )
            return dict(row) if row else None

    async def list(self) -> list[dict]:
        """List all sessions ordered by creation date descending."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, title, mode, created_at, updated_at FROM sessions ORDER BY created_at DESC"
            )
            return [dict(row) for row in rows]

    async def delete(self, session_id: str) -> bool:
        """Delete a session by ID. Returns True if a row was deleted."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM sessions WHERE id = $1",
                session_id,
            )
            return result == "DELETE 1"
