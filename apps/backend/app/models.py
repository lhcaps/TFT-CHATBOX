"""Pydantic models for request/response validation."""
from __future__ import annotations

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field


Mode = Literal["normal", "rag", "coach"]
Role = Literal["system", "user", "assistant", "tool"]


class SessionCreate(BaseModel):
    """Request to create a new session."""
    title: Optional[str] = None
    mode: Mode = "normal"


class SessionOut(BaseModel):
    """Session response."""
    id: str
    title: Optional[str] = None
    mode: Mode


class MessageOut(BaseModel):
    """Message response."""
    role: Role
    content: str
    citations: list[dict[str, Any]] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Chat request."""
    session_id: Optional[str] = None
    message: str
    mode: Mode = "rag"
    top_k: int = 6
    patch: Optional[str] = None
    season: Optional[str] = None
    stream: bool = True


class SearchRequest(BaseModel):
    """Search request for RAG retrieval."""
    query: str
    top_k: int = 8
    patch: Optional[str] = None


class ChunkResult(BaseModel):
    """Single retrieved chunk in a search result."""
    id: str
    source: str
    heading: str = ""
    text: str
    score: float


class SearchResult(BaseModel):
    """Response from the search endpoint."""
    query: str
    top_k: int
    patch: Optional[str] = None
    chunks: list[ChunkResult]
    count: int
