"""Session management endpoints."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.models import SessionCreate, SessionOut

router = APIRouter(prefix="/sessions", tags=["sessions"])

# In-memory store for MVP (replace with DB in Phase 2)
_sessions: dict[str, dict] = {}


@router.post("", response_model=SessionOut)
async def create_session(body: SessionCreate) -> SessionOut:
    """Create a new chat session."""
    session_id = uuid.uuid4().hex[:8]
    session = {
        "id": session_id,
        "title": body.title or f"Session {session_id}",
        "mode": body.mode,
        "messages": [],
    }
    _sessions[session_id] = session
    return SessionOut(**session)


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: str) -> SessionOut:
    """Get a session by ID."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionOut(**_sessions[session_id])


@router.get("", response_model=list[SessionOut])
async def list_sessions() -> list[SessionOut]:
    """List all sessions."""
    return [SessionOut(**s) for s in _sessions.values()]


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict[str, str]:
    """Delete a session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    del _sessions[session_id]
    return {"deleted": session_id}
