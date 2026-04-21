"""Message repository for database persistence."""
from __future__ import annotations

from typing import Optional

import asyncpg


class MessageRepository:
    """Repository for message CRUD operations."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def create(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Create a new message in a session."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO messages (session_id, role, content, metadata)
                VALUES ($1, $2, $3, $4)
                RETURNING id, session_id, role, content, metadata, created_at
                """,
                session_id,
                role,
                content,
                metadata or {},
            )
            return dict(row)

    async def get_recent(self, session_id: str, limit: int) -> list[dict]:
        """Get the most recent N messages for a session in chronological order.
        
        Excludes system messages from the window so the system prompt is never
        counted against the history limit.
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT role, content FROM messages
                WHERE session_id = $1 AND role != 'system'
                ORDER BY created_at DESC
                LIMIT $2
                """,
                session_id,
                limit,
            )
            return [dict(r) for r in reversed(rows)]

    async def create_system(self, session_id: str, content: str) -> dict:
        """Create a system message in a session."""
        return await self.create(session_id, "system", content)
