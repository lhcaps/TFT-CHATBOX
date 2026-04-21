"""Message repository for database persistence."""
from __future__ import annotations

import json
from typing import Optional

from asyncpg import Pool


class MessageRepository:
    """Repository for message CRUD operations using asyncpg."""

    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def create(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Create a new message and return it as a dict."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO messages (session_id, role, content, metadata)
                VALUES ($1, $2, $3, $4::jsonb)
                RETURNING id, session_id, role, content, metadata, created_at
                """,
                session_id,
                role,
                content,
                json.dumps(metadata or {}),
            )
            return dict(row)

    async def get_recent(self, session_id: str, limit: int) -> list[dict]:
        """Get recent messages for a session, excluding system messages.

        Returns messages in chronological order (oldest first).
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
            return [dict(row) for row in reversed(rows)]

    async def create_system(self, session_id: str, content: str) -> dict:
        """Create a system message for a session."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO messages (session_id, role, content)
                VALUES ($1, 'system', $2)
                RETURNING id, session_id, role, content, metadata, created_at
                """,
                session_id,
                content,
            )
            return dict(row)
