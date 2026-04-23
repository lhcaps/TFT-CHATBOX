"""Graph knowledge base API endpoints."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.graph import knowledge_graph
from app.graph.events import trigger_reload
from app.graph.models import (
    GraphQueryResponse,
    NeighborResponse,
    NeighborItem,
    ErrorResponse,
    IngestResponse,
    NodeCounts,
)

router = APIRouter(prefix="/graph", tags=["graph"])
logger = logging.getLogger(__name__)

# Shared normalization — same logic as builder.normalize_id
_normalize_pattern = re.compile(r"[^a-z0-9]+")


def normalize(name: str) -> str:
    """Normalize entity name to graph node ID."""
    return _normalize_pattern.sub("_", name.lower().strip()).strip("_")


def _get_suggestions(G, query: str, limit: int = 5) -> list[str]:
    """Get fuzzy-suggested entity names for 404 responses."""
    normalized = normalize(query)
    matches = [n for n in G.nodes() if normalized in n]
    matches.sort(key=len)
    return matches[:limit]


import networkx as nx

def _traverse(G, entity_id: str, relation: Optional[str], depth: int, limit: int):
    """Traverse graph up to depth, filtering by edge type."""
    results = []
    traversal = dict(nx.single_source_shortest_path_length(G, entity_id, cutoff=depth))
    for neighbor in traversal:
        if neighbor == entity_id:
            continue
        edge_data = G.get_edge_data(entity_id, neighbor) or {}
        for edge_key, attrs in edge_data.items():
            edge_type = attrs.get("edge_type", "neighbor")
            if relation and edge_type != relation:
                continue
            results.append({
                "type": edge_type,
                "target": G.nodes[neighbor].get("name", neighbor),
                "metadata": {k: v for k, v in attrs.items() if k != "edge_type"},
            })
            if len(results) >= limit:
                return results
    return results


def _get_neighbors(G, entity_id: str, types_filter: Optional[str], limit: int):
    """Get direct neighbors, optionally filtered by node type."""
    neighbors = []
    type_set = set(types_filter.split(",")) if types_filter else None

    for neighbor in G.neighbors(entity_id):
        node_data = G.nodes[neighbor]
        if type_set and node_data.get("type") not in type_set:
            continue
        edge_data = next(iter((G.get_edge_data(entity_id, neighbor) or {}).values()), {})
        neighbors.append(NeighborItem(
            node=node_data.get("name", neighbor),
            type=node_data.get("type", "unknown"),
            edge=edge_data.get("edge_type", "neighbor"),
            count=edge_data.get("count"),
        ))
        if len(neighbors) >= limit:
            break
    return neighbors


@router.get("/query", response_model=GraphQueryResponse)
async def query_graph(
    entity: str = Query(..., description="Node name to query"),
    relation: Optional[str] = Query(None, description="Edge type filter (e.g. HAS_TRAIT)"),
    depth: int = Query(1, ge=1, le=3, description="Traversal depth (max 3)"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
) -> GraphQueryResponse:
    """Query the knowledge graph for neighbors or traversed paths.
    
    Example: GET /api/graph/query?entity=Briar&relation=HAS_TRAIT&depth=1
    """
    G = knowledge_graph.get()
    entity_id = normalize(entity)

    if entity_id not in G:
        suggestions = _get_suggestions(G, entity)
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="Entity not found",
                entity=entity,
                suggestions=suggestions,
            ).model_dump(),
        )

    results = _traverse(G, entity_id, relation, depth, limit)
    return GraphQueryResponse(
        entity=entity,
        query="traversal",
        results=results,
        total=len(results),
    )


@router.get("/neighbors/{entity_name}", response_model=NeighborResponse)
async def get_neighbors(
    entity_name: str,
    types: Optional[str] = Query(None, description="Comma-separated node types (champion,item,trait,augment,system)"),
    limit: int = Query(10, ge=1, le=50, description="Max neighbors to return"),
) -> NeighborResponse:
    """Get all direct neighbors of an entity.
    
    Example: GET /api/graph/neighbors/Briar?types=item,trait
    """
    G = knowledge_graph.get()
    entity_id = normalize(entity_name)

    if entity_id not in G:
        suggestions = _get_suggestions(G, entity_name)
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="Entity not found",
                entity=entity_name,
                suggestions=suggestions,
            ).model_dump(),
        )

    neighbors = _get_neighbors(G, entity_id, types, limit)
    return NeighborResponse(entity=entity_name, neighbors=neighbors)


@router.post("/reload", response_model=IngestResponse)
async def reload_graph() -> IngestResponse:
    """Hot-reload the graph from JSON files.
    
    Rebuilds the entire graph from source JSON files.
    Also triggers cache invalidation via registered callbacks.
    """
    logger.info("Manual graph reload requested via /api/graph/reload")
    trigger_reload()

    counts = NodeCounts(**knowledge_graph.node_counts)
    return IngestResponse(
        reloaded=True,
        node_counts=counts,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_graph(
    source: str = Query("all", description="Source to reload: all, champions, items, traits, augments, systems"),
) -> IngestResponse:
    """Reload graph data from all sources.
    
    This is the same as POST /api/graph/reload but follows the naming
    convention expected by the ingest pipeline.
    """
    logger.info(f"Graph ingest requested for source: {source}")
    trigger_reload()

    counts = NodeCounts(**knowledge_graph.node_counts)
    return IngestResponse(
        reloaded=True,
        node_counts=counts,
        timestamp=datetime.utcnow().isoformat(),
    )
