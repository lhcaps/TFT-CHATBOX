"""Session management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import get_pool
from app.models import SessionCreate, SessionOut
from app.repositories import SessionRepository

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def get_session_repo() -> SessionRepository:
    """Get a SessionRepository instance."""
    pool = await get_pool()
    return SessionRepository(pool)


@router.post("", response_model=SessionOut)
async def create_session(body: SessionCreate) -> SessionOut:
    """Create a new chat session."""
    repo = await get_session_repo()
    session = await repo.create(title=body.title, mode=body.mode)
    return SessionOut(**session)


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: str) -> SessionOut:
    """Get a session by ID."""
    repo = await get_session_repo()
    session = await repo.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionOut(**session)


@router.get("", response_model=list[SessionOut])
async def list_sessions() -> list[SessionOut]:
    """List all sessions."""
    repo = await get_session_repo()
    sessions = await repo.list()
    return [SessionOut(**s) for s in sessions]


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict[str, str]:
    """Delete a session."""
    repo = await get_session_repo()
    deleted = await repo.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": session_id}
