"""Pydantic models for request/response validation."""
from __future__ import annotations

import re
from typing import Literal, Optional, Any

from pydantic import BaseModel, Field, field_validator


Mode = Literal["normal", "rag", "coach"]
Role = Literal["system", "user", "assistant", "tool"]

# Format-agnostic UUID pattern (matches both strict UUIDs and nanoid-style IDs)
_SessionIdPattern = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")


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
    top_k: int = Field(default=6, ge=1, le=50, description="Number of context chunks to retrieve (1–50)")
    patch: Optional[str] = None
    season: Optional[str] = None
    stream: bool = True

    @field_validator("session_id")
    @classmethod
    def session_id_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not _SessionIdPattern.match(v):
            raise ValueError("session_id must be 8–64 alphanumeric characters, hyphens, or underscores")
        return v


class SearchRequest(BaseModel):
    """Search request for RAG retrieval."""
    query: str
    top_k: int = Field(default=8, ge=1, le=50, description="Number of chunks to retrieve (1–50)")
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
