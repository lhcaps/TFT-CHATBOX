"""Pydantic models for graph API request/response validation."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class GraphQueryResponse(BaseModel):
    entity: str
    query: str
    results: list[dict] = Field(default_factory=list)
    total: int = 0


class NeighborItem(BaseModel):
    node: str
    type: str
    edge: Optional[str] = None
    count: Optional[int] = None


class NeighborResponse(BaseModel):
    entity: str
    neighbors: list[NeighborItem] = Field(default_factory=list)


class NodeCounts(BaseModel):
    champion: int = 0
    item: int = 0
    trait: int = 0
    augment: int = 0
    god: int = 0
    system: int = 0


class IngestResponse(BaseModel):
    reloaded: bool
    node_counts: NodeCounts
    timestamp: str


class ErrorResponse(BaseModel):
    error: str
    entity: str
    suggestions: list[str] = Field(default_factory=list)
