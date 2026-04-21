"""Session management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import get_pool
from app.models import SessionCreate, SessionOut, MessageOut
from app.repositories import SessionRepository, MessageRepository

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def _session_repo() -> SessionRepository:
    pool = await get_pool()
    return SessionRepository(pool)


async def _message_repo() -> MessageRepository:
    pool = await get_pool()
    return MessageRepository(pool)


@router.get("", response_model=list[SessionOut])
async def list_sessions() -> list[SessionOut]:
    """List all sessions."""
    repo = await _session_repo()
    sessions = await repo.list()
    return [SessionOut(**s) for s in sessions]


@router.post("", response_model=SessionOut)
async def create_session(body: SessionCreate) -> SessionOut:
    """Create a new chat session."""
    repo = await _session_repo()
    session = await repo.create(title=body.title, mode=body.mode)
    return SessionOut(**session)


# NOTE: must be declared before /{session_id} to avoid path conflict
@router.get("/{session_id}/messages", response_model=list[MessageOut])
async def get_session_messages(session_id: str) -> list[MessageOut]:
    """Get all messages for a session in chronological order."""
    repo = await _message_repo()
    messages = await repo.get_all(session_id)
    return [MessageOut(**m) for m in messages]


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: str) -> SessionOut:
    """Get a session by ID."""
    repo = await _session_repo()
    session = await repo.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionOut(**session)


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict[str, str]:
    """Delete a session and all its messages."""
    repo = await _session_repo()
    deleted = await repo.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": session_id}
