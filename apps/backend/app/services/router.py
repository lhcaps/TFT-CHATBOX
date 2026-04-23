"""Query routing service: graph-first, RAG fallback, MetaTFT enrichment."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class QuerySource(str, Enum):
    GRAPH = "graph"      # Knowledge graph — hard facts (stats, recipes, breakpoints)
    RAG = "rag"          # RAG retrieval — patch notes, strategy text
    METATFT = "metatft"  # MetaTFT data — comps, tier lists, win rates


@dataclass
class RoutedQuery:
    """Result of query routing."""
    text: str
    sources: list[QuerySource]
    graph_data: Optional[dict] = None  # Graph traversal results
    rag_chunks: list[dict] = field(default_factory=list)  # RAG results
    metatft_data: Optional[dict] = None  # MetaTFT comp data
    attribution: list[str] = field(default_factory=list)  # Source attribution text


# ─── Query Classification ──────────────────────────────────────────────────────

# Patterns that indicate graph-first queries (entity lookups)
GRAPH_PATTERNS = [
    re.compile(r"items?\s+(for|on|with)\s+\w+", re.IGNORECASE),        # "items for Briar"
    re.compile(r"best\s+items?", re.IGNORECASE),                       # "best items"
    re.compile(r"traits?\s+(for|on|with)\s+\w+", re.IGNORECASE),     # "traits for Soraka"
    re.compile(r"\w+\s+trait", re.IGNORECASE),                        # "Anima trait"
    re.compile(r"breakpoint", re.IGNORECASE),                          # "Anima breakpoint"
    re.compile(r"recipe\s+(for|of)\s+\w+", re.IGNORECASE),           # "recipe for IE"
    re.compile(r"build\s+(from|with)\s+\w+", re.IGNORECASE),         # "build from B.F.Sword"
    re.compile(r"rolling\s+odds", re.IGNORECASE),                     # "rolling odds"
    re.compile(r"compare\s+\w+\s+vs\.?\s+\w+", re.IGNORECASE),       # "compare IE vs GS"
    re.compile(r"augment\s+\w+", re.IGNORECASE),                     # "augment options"
    re.compile(r"is\s+\w+\s+good", re.IGNORECASE),                   # "is Anima good"
    re.compile(r"cost\s+\d", re.IGNORECASE),                          # "3-cost champions"
    re.compile(r"counters?\s+(for|against)?\s*\w+", re.IGNORECASE),  # "counters for Briar"
]

# Patterns that indicate meta/comps queries (MetaTFT/RAG)
METATFT_PATTERNS = [
    re.compile(r"top\s+comps?", re.IGNORECASE),                       # "top comps"
    re.compile(r"best\s+comp", re.IGNORECASE),                       # "best comp"
    re.compile(r"meta", re.IGNORECASE),                              # "meta comps"
    re.compile(r"tier\s+(list)?", re.IGNORECASE),                   # "tier list"
    re.compile(r"win\s+rate", re.IGNORECASE),                       # "win rate"
    re.compile(r"play\s+rate", re.IGNORECASE),                      # "play rate"
]

# Patterns that indicate complex questions needing RAG
RAG_PATTERNS = [
    re.compile(r"how\s+to\s+(play|build)", re.IGNORECASE),          # "how to play"
    re.compile(r"strategy", re.IGNORECASE),                          # "strategy"
    re.compile(r"patch\s+notes?", re.IGNORECASE),                   # "patch notes"
    re.compile(r"when\s+to\s+(roll|level)", re.IGNORECASE),        # "when to roll"
    re.compile(r"should\s+i\s+(roll|level|sell)", re.IGNORECASE),   # "should I roll"
]


def classify_query(query: str) -> tuple[list[QuerySource], list[str]]:
    """Classify a query and return ordered list of sources to query + detected entities."""
    sources: list[QuerySource] = []
    detected_entities: list[str] = []

    query_lower = query.lower()

    # Check for graph-first patterns (entity lookups)
    for pattern in GRAPH_PATTERNS:
        if pattern.search(query):
            if QuerySource.GRAPH not in sources:
                sources.insert(0, QuerySource.GRAPH)
            match = pattern.search(query)
            if match:
                words = match.group(0).split()
                if len(words) > 1:
                    detected_entities.append(words[-1])

    # Check for meta/comps patterns (MetaTFT)
    for pattern in METATFT_PATTERNS:
        if pattern.search(query):
            if QuerySource.METATFT not in sources:
                sources.append(QuerySource.METATFT)
            if QuerySource.RAG not in sources:
                sources.append(QuerySource.RAG)

    # Check for complex question patterns (RAG)
    for pattern in RAG_PATTERNS:
        if pattern.search(query):
            if QuerySource.RAG not in sources:
                sources.append(QuerySource.RAG)

    # Default: graph + rag if nothing detected
    if not sources:
        sources = [QuerySource.GRAPH, QuerySource.RAG]

    return sources, detected_entities


# ─── Router Implementation ──────────────────────────────────────────────────────

class QueryRouter:
    """Routes queries to appropriate knowledge sources and merges results."""

    def __init__(self):
        self._graph = None  # Lazy import to avoid circular deps
        self._retrieval = None

    @property
    def graph(self):
        if self._graph is None:
            from app.graph import knowledge_graph
            self._graph = knowledge_graph.get()
        return self._graph

    async def route(self, query: str, top_k: int = 6) -> RoutedQuery:
        """Route a query to appropriate sources and return merged results."""
        sources, entities = classify_query(query)

        result = RoutedQuery(text=query, sources=sources)

        for source in sources:
            if source == QuerySource.GRAPH:
                result.graph_data = await self._query_graph(query, entities)
                if result.graph_data:
                    result.attribution.append("graph")
            elif source == QuerySource.RAG:
                result.rag_chunks = await self._query_rag(query, top_k)
                if result.rag_chunks:
                    result.attribution.append("rag")
            elif source == QuerySource.METATFT:
                result.metatft_data = await self._query_metatft(query)
                if result.metatft_data:
                    result.attribution.append("metatft")

        return result

    async def _query_graph(self, query: str, entities: list[str]) -> dict | None:
        """Query knowledge graph for entity information."""
        try:
            for entity in entities:
                normalized = _normalize(entity)
                if normalized in self.graph:
                    neighbors = []
                    for neighbor in self.graph.neighbors(normalized):
                        node_data = self.graph.nodes[neighbor]
                        edge_data = next(
                            iter((self.graph.get_edge_data(normalized, neighbor) or {}).values()), {}
                        )
                        neighbors.append({
                            "node": node_data.get("name", neighbor),
                            "type": node_data.get("type", "unknown"),
                            "edge": edge_data.get("edge_type", "neighbor"),
                            "count": edge_data.get("count"),
                        })
                        if len(neighbors) >= 10:
                            break
                    return {"entity": entity, "neighbors": neighbors, "total": len(neighbors)}
        except Exception as e:
            logger.warning(f"Graph query failed: {e}")
        return None

    async def _query_rag(self, query: str, top_k: int) -> list[dict]:
        """Query RAG retrieval for complex questions."""
        try:
            from app.services.retrieval import retrieve_chunks
            return await retrieve_chunks(query, mode="rag", top_k=top_k)
        except Exception as e:
            logger.warning(f"RAG query failed: {e}")
        return []

    async def _query_metatft(self, query: str) -> dict | None:
        """Query MetaTFT data for comps/tier lists."""
        # MetaTFT data is in RAG chunks with source="metatft"
        # This is handled by _query_rag filtering by source
        return None  # Handled by RAG filtering


# Shared normalization — same logic as routes/graph.normalize
_normalize_pattern = re.compile(r"[^a-z0-9]+")


def _normalize(name: str) -> str:
    """Normalize entity name to graph node ID."""
    return _normalize_pattern.sub("_", name.lower().strip()).strip("_")
