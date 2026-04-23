# Phase 11: TFT Knowledge Graph - Research

**Researched:** 2026-04-23
**Domain:** NetworkX graph database + FastAPI backend integration
**Confidence:** HIGH

## Summary

Phase 11 builds an in-memory directed multigraph from 8 verified Set 17 JSON files using NetworkX. The graph enables cross-entity traversals: "best items for Briar?" → graph traversal → champion → trait → item edges. The data model is locked via CONTEXT.md decisions — research focuses on implementation approach, NetworkX API, API design patterns, and testing strategy.

**Primary recommendation:** Use `nx.MultiDiGraph` with a `LazyGraphLoader` singleton. Add NetworkX as a project dependency. Build edge-by-edge from JSON, starting with `HAS_TRAIT` (from deep_pack_v4 origins/classes) and `BUILDS_FROM` (from items_formulas). ITEM_FOR_CHAMPION uses cost/trait heuristics. Register the FastAPI router in `main.py`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Graph construction | API/Backend | — | NetworkX runs in FastAPI worker process |
| JSON loading | API/Backend | — | File I/O in service layer |
| Neighbor queries | API/Backend | Browser/Client | API returns structured JSON; frontend renders cards |
| Auto-reload signal | API/Backend | — | Ingest endpoint emits event → graph rebuilds |
| Cache invalidation | API/Backend | — | Embedding cache cleared after reload |

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Primary champion source:** `tft_set17_patch17_1_deep_pack_v4_user_verified.json` — 59 champions with `traits_numeric.origins` and `traits_numeric.classes`
- **Edge strategy:** Conservative — HAS_TRAIT, BUILDS_FROM, ITEM_FOR_CHAMPION only. SYNERGIZES/COUNTERS/COUNTERED_BY NOT built
- **Trait classification:** Origin/class from `traits_numeric.origins` vs `traits_numeric.classes` keys in deep_pack_v4
- **Partial data:** Include items with `completeness: "partial"` — add `is_verified` attribute to nodes
- **Loading:** Lazy-load on first API query, NOT on backend startup
- **No serialization:** Rebuild from JSON each time
- **Node IDs:** lowercase normalized (e.g., "briar", "bloodthirster")
- **God IDs:** suffix `_god` (e.g., "soraka_god") to avoid champion collision
- **Graph type:** `nx.MultiDiGraph`

### Claude's Discretion
- Exact heuristics for ITEM_FOR_CHAMPION (cost/trait → carry/tank/support role mapping)
- How to normalize champion names with special characters
- Exact format of neighbors response (include edge weights or not)
- Integration approach with existing cache service

### Deferred Ideas (OUT OF SCOPE)
- SYNERGIZES/COUNTERS/COUNTERED_BY — no reliable meta data
- GOD_ALIGNMENT — no god↔trait links in current files
- ITEM_INTO — no upgrade chain data

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| KNOW-01 | NetworkX knowledge graph with Champion/Item/Trait/Augment/God/System nodes | NetworkX MultiDiGraph model, node attribute schema, edge construction from 8 JSON sources |
| KNOW-02 | `/api/graph/query` + `/api/graph/neighbors/{entity}` endpoints | FastAPI router pattern, Pydantic response models, error handling with suggestions |
| KNOW-03 | Auto-reload on patch ingest + hot-reload endpoint | Event signal from ingest pipeline, POST /api/graph/reload, embedding cache invalidation |
| KNOW-04 | Unit tests for graph traversals | pytest fixture strategy, minimum node counts, edge cases, <5s runtime |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `networkx` | 3.3 | Graph data structure + traversal algorithms | Standard Python graph library, handles MultiDiGraph, fast in-memory operations |
| `fastapi` | (existing) | REST API framework | Already in project |
| `pydantic` | (existing) | Request/response validation | Already in project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | (existing) | Test framework | Unit tests in `tests/test_graph.py` |
| `pytest-asyncio` | (existing) | Async test support | If testing async reload behavior |

**Installation:**
```bash
pip install networkx
```

**Version verification:**
```bash
pip show networkx
# Expected: 3.3+ (current stable as of 2026-01)
```

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `nx.MultiDiGraph` | `nx.DiGraph` | MultiDiGraph needed if multiple HAS_TRAIT edges between same champion-trait pair (shouldn't happen, but defensive) |
| NetworkX | `igraph` | NetworkX has better Python integration, more traversal algorithms, larger ecosystem |
| NetworkX | `redis-graph` | Overkill — no persistence needed, data fits in memory |
| Lazy loading | Eager loading on startup | CONTEXT.md locks lazy-load; startup should not be blocked |

---

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Backend Process                                 │
│  ┌─────────────┐    ┌─────────────────────────────────────────────┐    │
│  │ FastAPI     │    │           LazyGraphLoader (singleton)         │    │
│  │ /api/graph/*│───▶│  ┌─────────────────────────────────────────┐ │    │
│  │ endpoints   │    │  │         nx.MultiDiGraph                 │ │    │
│  └─────────────┘    │  │  ┌──────┐     ┌──────┐     ┌──────┐   │ │    │
│          ▲           │  │  │Node  │────▶│Node  │◀────│Node  │   │ │    │
│          │           │  │  └──────┘     └──────┘     └──────┘   │ │    │
│  ┌───────────────┐  │  └─────────────────────────────────────────┘ │    │
│  │ Ingest        │  │                                              │    │
│  │ Pipeline      │──┼──▶ Event signal → graph.reload()              │    │
│  └───────────────┘  │  ┌─────────────────────────────────────────┐ │    │
│                     │  │         JSON Data Sources (8 files)        │ │    │
│                     │  │  deep_pack_v4 / items_formulas / augments │ │    │
│                     │  └─────────────────────────────────────────┘ │    │
│                     └─────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌────────────────────┐           │                                     │
│  │ Embedding Cache    │◀──────────┘ (invalidate on reload)              │
│  │ (app.services.cache)│                                               │
│  └────────────────────┘                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
apps/backend/
├── app/
│   ├── graph/
│   │   ├── __init__.py              # exports: knowledge_graph, LazyGraphLoader
│   │   ├── models.py                # Pydantic schemas: GraphQuery, NeighborResponse
│   │   ├── loader.py                # LazyGraphLoader class, load_champions(), etc.
│   │   ├── builder.py               # build_graph() — constructs nx.MultiDiGraph
│   │   └── heuristics.py            # ITEM_FOR_CHAMPION role detection logic
│   ├── routers/
│   │   └── graph.py                 # FastAPI router: /api/graph/*
│   └── services/
│       └── cache.py                 # embedding_cache.clear() on reload
├── tests/
│   ├── conftest.py                  # shared fixtures (empty graph, sample JSON)
│   └── test_graph.py               # all KNOW-04 tests
└── data/                            # symlinks or copies of verified JSON files
    ├── tft_set17_patch17_1_deep_pack_v4_user_verified.json
    ├── items_formulas_full_set17.json
    └── ...
```

### Pattern 1: LazyGraphLoader Singleton

**What:** Thread-safe lazy-loading wrapper around `nx.MultiDiGraph` that defers construction until first access.

**When to use:** Every API request to `/api/graph/*` routes through this singleton.

**Example:**
```python
# apps/backend/app/graph/__init__.py
from functools import lru_cache
from networkx import MultiDiGraph

class LazyGraphLoader:
    """Lazily builds the knowledge graph on first access."""
    _instance: "LazyGraphLoader | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._graph = None
            cls._instance._loaded = False
        return cls._instance

    def get(self) -> MultiDiGraph:
        if self._graph is None:
            self._graph = self._build()
            self._loaded = True
        return self._graph

    def reload(self) -> None:
        """Clear and rebuild the graph from JSON sources."""
        self._graph = None
        self._loaded = False
        # Force rebuild on next get()
        self.get()

    def _build(self) -> MultiDiGraph:
        from app.graph.builder import build_graph
        return build_graph()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

knowledge_graph = LazyGraphLoader()
```

### Pattern 2: GraphBuilder — Node and Edge Construction

**What:** Pure function `build_graph()` that loads all 8 JSON files and constructs the MultiDiGraph.

**Construction order:**
1. Load `deep_pack_v4` → create ChampionNode + TraitNode (from `origins`/`classes` keys) + SystemNode
2. Load `items_formulas` → create ItemNode + BUILDS_FROM edges + component nodes
3. Load `items_effects` → enrich ItemNode attributes (effect text, stats, is_verified)
4. Load `augments_full` → create AugmentNode
5. Load `traits_full` → enrich TraitNode (from champions list, breakpoints)
6. Load `enhanced_pack` → create GodNode + SystemNode
7. Load `rolling_odds` → create SystemNode
8. Build HAS_TRAIT edges (champion → trait with count)
9. Build ITEM_FOR_CHAMPION edges (heuristic role detection)
10. Build TRAIT_BREAKPOINT edges

**Example:**
```python
# apps/backend/app/graph/builder.py
import json
from pathlib import Path
from networkx import MultiDiGraph

def normalize_id(name: str) -> str:
    """Lowercase, strip whitespace, replace spaces with underscores."""
    return name.lower().strip().replace(" ", "_")

def load_json(filename: str) -> dict:
    base = Path(__file__).parent.parent.parent.parent  # apps/backend/
    with open(base / filename) as f:
        return json.load(f)

def build_graph() -> MultiDiGraph:
    G = MultiDiGraph()

    # 1. Champions + Traits from deep_pack_v4
    deep = load_json("tft_set17_patch17_1_deep_pack_v4_user_verified.json")

    # TraitNodes from origins
    for trait_name, trait_data in deep.get("traits_numeric", {}).get("origins", {}).items():
        node_id = normalize_id(trait_name)
        G.add_node(node_id,
            type="trait",
            name=trait_name,
            trait_type="origin",
            breakpoints=trait_data.get("breakpoints", []),
            description=trait_data.get("effect", ""),
            is_verified=True,
        )

    # TraitNodes from classes
    for trait_name, trait_data in deep.get("traits_numeric", {}).get("classes", {}).items():
        node_id = normalize_id(trait_name)
        if node_id not in G:
            G.add_node(node_id,
                type="trait",
                name=trait_name,
                trait_type="class",
                breakpoints=trait_data.get("breakpoints", []),
                description=trait_data.get("effect", ""),
                is_verified=True,
            )

    # ChampionNodes
    for champ in deep.get("champions", []):
        champ_id = normalize_id(champ["name"])
        G.add_node(champ_id,
            type="champion",
            name=champ["name"],
            cost=champ.get("cost"),
            traits=champ.get("traits", []),
            ability_summary=champ.get("ability_summary", ""),
            is_verified=True,
        )

        # HAS_TRAIT edges
        for trait_entry in champ.get("traits", []):
            if isinstance(trait_entry, str):
                trait_name, count = trait_entry, 1
            else:
                trait_name = trait_entry.get("name", "")
                count = trait_entry.get("count", 1)
            trait_id = normalize_id(trait_name)
            if trait_id in G:
                G.add_edge(champ_id, trait_id,
                    edge_type="HAS_TRAIT",
                    count=count,
                )

    # 2. Items from items_formulas
    formulas = load_json("items_formulas_full_set17.json")

    for comp_name in formulas.get("components", []):
        comp_id = normalize_id(comp_name)
        if comp_id not in G:
            G.add_node(comp_id,
                type="item",
                name=comp_name,
                category="component",
                is_verified=True,
            )

    for item in formulas.get("standard_combined_items", []):
        item_id = normalize_id(item["name"])
        G.add_node(item_id,
            type="item",
            name=item["name"],
            category="standard",
            recipe=item.get("recipe", []),
            stats=item.get("stats", []),
            is_verified=True,
        )
        # BUILDS_FROM edges
        recipe = item.get("recipe", [])
        if len(recipe) == 2:
            comp_a_id = normalize_id(recipe[0])
            comp_b_id = normalize_id(recipe[1])
            G.add_edge(item_id, comp_a_id, edge_type="BUILDS_FROM", role="component_a")
            G.add_edge(item_id, comp_b_id, edge_type="BUILDS_FROM", role="component_b")

    # 3. Augments
    augments = load_json("augments_full_user_verified.json")
    for aug in augments.get("augments", []):
        aug_id = normalize_id(aug["name"])
        G.add_node(aug_id,
            type="augment",
            name=aug["name"],
            tier=aug.get("tier"),
            description=aug.get("description", ""),
            is_verified=True,
        )

    # 4. ITEM_FOR_CHAMPION edges (heuristic)
    from app.graph.heuristics import assign_item_edges
    assign_item_edges(G, deep, formulas)

    return G
```

### Pattern 3: ITEM_FOR_CHAMPION Heuristics

**What:** Assign `ITEM_FOR_CHAMPION` edges based on champion role inferred from cost and traits.

**Heuristic logic:**
```python
# apps/backend/app/graph/heuristics.py
from networkx import MultiDiGraph

ITEM_CATEGORIES = {
    "AD": ["bloodthirster", "giant_slayer", "infinity_edge", "runnans_terror",
           "spear_of_shojin", "death_blade"],
    "AP": ["blue_buff", "rabbadons_deathcap", "archangels_staff", "jeweled_gauntlet",
           "shojin"],
    "TANK": ["bramble_vest", "sunfire_captain", "gargoyle_stoneplate",
             "adaptive_helm", "warmogs_armor"],
    "SUPPORT": ["chalice_of_power", "redemption", "mooness_grudges"],
}

TRAIT_ROLE_MAP = {
    # Anima/HP-focused → tank items
    "anima": "TANK",
    "primordian": "TANK",
    "vanguard": "TANK",
    "bastion": "TANK",
    # Invoker/Conduit → AP items
    "invoker": "AP",
    "conduit": "AP",
    # Rogue/Marauder/Sniper → AD items
    "rogue": "AD",
    "marauder": "AD",
    "sniper": "AD",
    "challenger": "AD",
}

def infer_role(cost: int, traits: list[str]) -> str:
    """Infer champion role from cost and traits."""
    trait_names = [t.lower() for t in traits]
    for trait in trait_names:
        if trait in TRAIT_ROLE_MAP:
            return TRAIT_ROLE_MAP[trait]
    # Cost-based fallback: 4-5 cost → carry (AD or AP), 1-2 cost → frontline
    if cost >= 4:
        return "AD"  # Default to AD carry; Phase 13 can refine
    return "TANK"

def assign_item_edges(G: MultiDiGraph, deep_pack: dict, formulas: dict) -> None:
    """Assign ITEM_FOR_CHAMPION edges based on heuristic role detection."""
    item_names_by_category: dict[str, list[str]] = {}

    for item in formulas.get("standard_combined_items", []):
        item_id = normalize_id(item["name"])
        category = categorize_item(item)  # AD/AP/TANK/SUPPORT from recipe
        if category not in item_names_by_category:
            item_names_by_category[category] = []
        item_names_by_category[category].append(item_id)

    for champ in deep_pack.get("champions", []):
        champ_id = normalize_id(champ["name"])
        if champ_id not in G:
            continue

        traits = champ.get("traits", [])
        cost = champ.get("cost", 3)
        role = infer_role(cost, traits)

        # Assign top 3 items from the appropriate category
        items_for_role = item_names_by_category.get(role, [])
        for item_id in items_for_role[:3]:  # Top 3 items
            G.add_edge(item_id, champ_id,
                edge_type="ITEM_FOR_CHAMPION",
                role=role,
                confidence="heuristic",
            )
```

### Pattern 4: FastAPI Router for Graph Endpoints

**What:** Standard FastAPI router following existing project patterns (`prefix="/api/graph"`, `tags=["graph"]`).

**Example:**
```python
# apps/backend/app/routers/graph.py
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.graph import knowledge_graph
from app.graph.models import (
    GraphQueryResponse,
    NeighborResponse,
    IngestResponse,
    ErrorResponse,
    EntityNotFoundResponse,
)
from app.services.cache import embedding_cache

router = APIRouter(prefix="/graph", tags=["graph"])
logger = logging.getLogger(__name__)


@router.get("/query", response_model=GraphQueryResponse)
async def query_graph(
    entity: str = Query(..., description="Node name to query"),
    relation: Optional[str] = Query(None, description="Edge type filter"),
    depth: int = Query(1, ge=1, le=3),
    limit: int = Query(10, ge=1, le=50),
) -> GraphQueryResponse:
    """Query the knowledge graph for neighbors or traversed paths."""
    G = knowledge_graph.get()
    entity_id = _normalize(entity)

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
    types: Optional[str] = Query(None, description="Comma-separated node types"),
    limit: int = Query(10, ge=1, le=50),
) -> NeighborResponse:
    """Get all direct neighbors of an entity."""
    G = knowledge_graph.get()
    entity_id = _normalize(entity_name)

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
    """Hot-reload the graph from JSON files."""
    logger.info("Reloading knowledge graph...")
    knowledge_graph.reload()
    G = knowledge_graph.get()
    counts = _count_nodes(G)

    # Invalidate embedding cache after reload
    embedding_cache.clear()

    from datetime import datetime
    return IngestResponse(
        reloaded=True,
        node_counts=counts,
        timestamp=datetime.utcnow().isoformat(),
    )


def _normalize(name: str) -> str:
    """Normalize entity name to graph node ID."""
    return name.lower().strip().replace(" ", "_")

def _get_suggestions(G, query: str, limit: int = 5) -> list[str]:
    """Get fuzzy-suggested entity names for 404 responses."""
    normalized = _normalize(query)
    # Simple prefix match — could enhance with fuzzy matching
    return [n for n in G.nodes() if normalized in n][:limit]

def _traverse(G, entity_id, relation, depth, limit):
    """Traverse graph up to depth, filtering by relation type."""
    import networkx as nx
    results = []
    for neighbor in nx.single_source_shortest_path_length(G, entity_id, cutoff=depth):
        if neighbor == entity_id:
            continue
        for edge_key, edge_data in G.get_edge_data(entity_id, neighbor, default={}).items():
            if relation is None or edge_data.get("edge_type") == relation:
                results.append({
                    "type": edge_data.get("edge_type", "neighbor"),
                    "target": G.nodes[neighbor].get("name", neighbor),
                    "metadata": {k: v for k, v in edge_data.items() if k != "edge_type"},
                })
                if len(results) >= limit:
                    return results
    return results

def _get_neighbors(G, entity_id, types_filter, limit):
    """Get direct neighbors, optionally filtered by node type."""
    neighbors = []
    type_set = set(types_filter.split(",")) if types_filter else None

    for neighbor in G.neighbors(entity_id):
        node_data = G.nodes[neighbor]
        if type_set and node_data.get("type") not in type_set:
            continue

        # Get edge data
        edge_data = next(iter(G.get_edge_data(entity_id, neighbor).values()), {})
        neighbors.append({
            "node": node_data.get("name", neighbor),
            "type": node_data.get("type", "unknown"),
            "edge": edge_data.get("edge_type", "neighbor"),
            "count": edge_data.get("count"),
        })
        if len(neighbors) >= limit:
            break
    return neighbors

def _count_nodes(G) -> dict[str, int]:
    """Count nodes by type."""
    from collections import Counter
    counts = Counter(G.nodes[n].get("type", "unknown") for n in G.nodes())
    return dict(counts)
```

### Pattern 5: Ingest Pipeline → Graph Reload Signal

**What:** After `POST /api/ingest/patch-notes` or `POST /api/ingest/metatft` completes, the graph should reload. Simple callback/event pattern.

**Implementation:** Use a module-level event system:

```python
# apps/backend/app/graph/events.py
from typing import Callable

_reload_callbacks: list[Callable[[], None]] = []

def on_graph_reload(callback: Callable[[], None]) -> None:
    """Register a callback to be called when the graph reloads."""
    _reload_callbacks.append(callback)

def trigger_reload() -> None:
    """Called by ingest pipeline after successful ingest."""
    knowledge_graph.reload()
    for cb in _reload_callbacks:
        cb()
```

**Integration in `routers/ingest.py`:**
```python
# After successful ingest in each endpoint:
from app.graph.events import trigger_reload
trigger_reload()  # Non-blocking: reloads graph + clears cache
```

### Anti-Patterns to Avoid
- **`nx.Graph` instead of `nx.MultiDiGraph`:** Multiple edges between same node pair (e.g., both HAS_TRAIT and ITEM_FOR_CHAMPION from item to champion) require MultiDiGraph
- **Eager loading on startup:** CONTEXT.md locks lazy-load — blocking startup with graph construction defeats the purpose
- **Serializing graph to disk:** No persistence needed per CONTEXT.md — rebuild from JSON each time is fast enough
- **Building SYNERGIZES/COUNTERS without data:** CONTEXT.md explicitly defers these — do not create heuristic synergy edges
- **Case-sensitive node IDs:** Champions/traits may be queried with different capitalization — normalize to lowercase with underscores

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|------------|-----|
| Graph data structure | Custom dict-of-dicts | `nx.MultiDiGraph` | Handles multi-edges, traversals, serialization natively |
| JSON loading | Manual `json.load()` per file scattered everywhere | Centralized `load_json()` in `builder.py` | Single point for error handling, path management |
| Fuzzy entity matching | Levenshtein distance from scratch | Simple substring match + prefix match (can upgrade to rapidfuzz later) | Enough for 404 suggestions; SW-01 can add fuzzy later |
| Graph reload signaling | Redis pub/sub or database table | Simple callback list in `events.py` | No external dependencies, synchronous, sufficient |

---

## Common Pitfalls

### Pitfall 1: Case-sensitivity in node lookups
**What goes wrong:** User queries "Briar" but graph node is "briar" → 404.
**Why it happens:** Node IDs are lowercase normalized; API accepts raw names.
**How to avoid:** Always normalize in `_normalize()` helper; normalize before `G.nodes()` lookup.
**Warning signs:** 404 on champion names that exist in JSON files.

### Pitfall 2: Trait names with special characters
**What goes wrong:** Trait "N.O.V.A." normalizes to "n_o_v_a_" which is ugly; SPACE GROOVE → "space_groove".
**Why it happens:** `str.replace(" ", "_")` handles spaces but dots/punctuation need special handling.
**How to avoid:** Use `re.sub(r'[^a-z0-9]+', '_', name.lower().strip())` for normalization that collapses all non-alphanumeric to underscores.
**Warning signs:** Trailing underscores in node IDs, multiple underscores in a row.

### Pitfall 3: Missing node causing KeyError
**What goes wrong:** Champion has trait "Anima" but Anima trait node hasn't been added yet.
**Why it happens:** Order of node/edge creation matters — traits should be added before champion edges reference them.
**How to avoid:** Add all TraitNodes first (from origins + classes keys), then all ChampionNodes with HAS_TRAIT edges. Use `if trait_id in G` guard.
**Warning signs:** `KeyError` or `NodeNotFound` errors when building edges.

### Pitfall 4: Large JSON files blocking event loop
**What goes wrong:** `json.load()` on 3500-line deep_pack_v4 blocks FastAPI async event loop.
**Why it happens:** JSON loading is CPU-bound, not async-aware.
**How to avoid:** Load JSON files in a thread pool via `asyncio.to_thread()` in the reload endpoint, or load synchronously during lazy init (not on async request path). The `_build()` method runs synchronously but only once.
**Warning signs:** API requests timeout during first graph query.

### Pitfall 5: Embedding cache not invalidated after reload
**What goes wrong:** New patch data ingested but RAG still returns old chunks because embeddings are cached.
**Why it happens:** `embedding_cache.clear()` not called after graph reload.
**How to avoid:** Call `embedding_cache.clear()` in `reload_graph()` endpoint AND in `trigger_reload()` callback from ingest pipeline.

---

## Code Examples

### Normalizing node IDs consistently

```python
import re

def normalize_id(name: str) -> str:
    """Lowercase, strip, collapse non-alphanumeric to underscores."""
    return re.sub(r'[^a-z0-9]+', '_', name.lower().strip()).strip('_')

# "N.O.V.A." → "n_o_v_a"
# "B.F. Sword" → "b_f_sword"
# "Bloodthirster" → "bloodthirster"
# "soraka" → "soraka"
```

### Querying neighbors with edge attributes

```python
import networkx as nx

G = knowledge_graph.get()
champ_id = normalize_id("Briar")

# Get all outgoing neighbors with edge data
for neighbor in G.neighbors(champ_id):
    edge_data = G.get_edge_data(champ_id, neighbor)
    for edge_key, attrs in edge_data.items():
        print(f"Briar --[{attrs['edge_type']}]--> {neighbor}")
        if attrs.get('count'):
            print(f"  count={attrs['count']}")
```

### Filtering traversal by edge type

```python
def get_trait_neighbors(G, champion_name):
    champ_id = normalize_id(champion_name)
    traits = []
    for neighbor in G.neighbors(champ_id):
        edge_data = G.get_edge_data(champ_id, neighbor)
        for attrs in edge_data.values():
            if attrs.get('edge_type') == 'HAS_TRAIT':
                traits.append({
                    'name': G.nodes[neighbor].get('name'),
                    'count': attrs.get('count', 1),
                })
    return traits
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw text search for entity relationships | NetworkX graph traversal | Phase 11 | Enables structured queries: "items for champion" → graph edges |
| No cross-entity linking | Graph with typed edges (HAS_TRAIT, BUILDS_FROM, ITEM_FOR_CHAMPION) | Phase 11 | LLM can traverse relationships instead of just retrieving text |
| Full graph rebuild on startup | Lazy-load on first query | Phase 11 | Startup is not blocked; graph loads when first API call arrives |

**Deprecated/outdated:**
- None relevant to Phase 11.

---

## Assumptions Log

> List all claims tagged `[ASSUMED]` in this research. The planner and discuss-phase use this section to identify decisions that need user confirmation before execution.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `deep_pack_v4_user_verified.json` contains a `champions` array at the top level (not nested) | Standard Stack | If champions are nested differently, builder needs adjustment. Verified from file read — champions array present at root level after `traits_numeric` |
| A2 | `items_effects_expanded_set17.json` components array contains `{name, effect, completeness}` objects | Common Pitfalls | If components are strings, normalization logic needs adjustment |
| A3 | NetworkX 3.3+ is compatible with existing Python version | Standard Stack | Version check should confirm on first install |
| A4 | `traits_full_user_verified.json` keys match trait names in deep_pack_v4 | Don't Hand-Roll | If names don't match (e.g., "Meeple" vs "Astronaut"), cross-reference enrichment will fail |
| A5 | `normalized_id("soraka")` for God node should be `"soraka_god"` — no collision with champion `"soraka"` | Architecture Patterns | If graph uses same ID space for all nodes, suffix is necessary. Verified: MultiDiGraph shares namespace |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

---

## Open Questions

1. **Champion ability summaries in deep_pack_v4**
   - What we know: `deep_pack_v4.champions` array has champion objects with at least `name`, `cost`, `traits`
   - What's unclear: Whether `ability_summary` field exists in all champion objects or only some
   - Recommendation: Use `.get("ability_summary", "")` as fallback; Phase 11 can enrich later from `data_pack.json`

2. **Enhanced_pack Space Gods detail level**
   - What we know: 9 Space Gods with `name` and `focus` fields
   - What's unclear: Whether reward tiers are available (not in enhanced_pack excerpt, might be in enhanced_report.md)
   - Recommendation: Add GodNode with available data now; leave `reward_tiers` empty dict if not present

3. **God ↔ Trait alignment**
   - What we know: `enhanced_pack` has 9 gods with `focus` fields (e.g., "HP preservation")
   - What's unclear: Whether to auto-link gods to matching traits (e.g., Soraka's "HP focus" → Anima trait)
   - Recommendation: DO NOT build GOD_ALIGNMENT edges per CONTEXT.md — this is deferred

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `networkx` | KNOW-01 graph construction | ✗ | — | Install via `pip install networkx` |
| `pytest` | KNOW-04 unit tests | ✓ | existing | — |
| JSON files | Graph construction | ✓ | 8 files verified | None (blocking) |
| `pydantic` | API models | ✓ | existing | — |
| `fastapi` | API endpoints | ✓ | existing | — |

**Missing dependencies with no fallback:**
- `networkx` — must be installed. Add to `requirements.txt` or `pyproject.toml`.

**Missing dependencies with fallback:**
- None identified.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `apps/backend/pytest.ini` (if exists) or `pyproject.toml` |
| Quick run command | `pytest apps/backend/tests/test_graph.py -x -v` |
| Full suite command | `pytest apps/backend/tests/test_graph.py -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|------------------|-------------|
| KNOW-01 | Graph loads with all 6 node types (champion, item, trait, augment, god, system) | unit | `pytest tests/test_graph.py::test_graph_loads_all_node_types -x` | ❌ Wave 0 |
| KNOW-01 | Graph has minimum node counts (≥59 champion, ≥30 trait, ≥45 item, ≥252 augment) | unit | `pytest tests/test_graph.py::test_graph_minimum_node_counts -x` | ❌ Wave 0 |
| KNOW-01 | Node attributes include is_verified flag | unit | `pytest tests/test_graph.py::test_node_attributes -x` | ❌ Wave 0 |
| KNOW-02 | `/api/graph/query` returns neighbors for valid entity | integration | `pytest tests/test_graph.py::test_query_returns_neighbors -x` | ❌ Wave 0 |
| KNOW-02 | `/api/graph/neighbors/{entity}` returns filtered results | integration | `pytest tests/test_graph.py::test_neighbors_filter_by_type -x` | ❌ Wave 0 |
| KNOW-02 | Missing entity returns 404 with suggestions | integration | `pytest tests/test_graph.py::test_missing_entity_404 -x` | ❌ Wave 0 |
| KNOW-03 | `POST /api/graph/reload` rebuilds graph and returns counts | integration | `pytest tests/test_graph.py::test_reload_rebuilds_graph -x` | ❌ Wave 0 |
| KNOW-03 | Reload invalidates embedding cache | unit | `pytest tests/test_graph.py::test_reload_clears_cache -x` | ❌ Wave 0 |
| KNOW-04 | HAS_TRAIT edge: Briar → Anima with count=1 | unit | `pytest tests/test_graph.py::test_has_trait_edges -x` | ❌ Wave 0 |
| KNOW-04 | BUILDS_FROM edge: Bloodthirster → B.F. Sword + Negatron Cloak | unit | `pytest tests/test_graph.py::test_builds_from_edges -x` | ❌ Wave 0 |
| KNOW-04 | Circular references handled (A↔B edges) | unit | `pytest tests/test_graph.py::test_circular_references -x` | ❌ Wave 0 |
| KNOW-04 | Empty champion traits handled | unit | `pytest tests/test_graph.py::test_empty_traits -x` | ❌ Wave 0 |
| KNOW-04 | Depth-3 traversal without infinite loop | unit | `pytest tests/test_graph.py::test_depth_limited_traversal -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest apps/backend/tests/test_graph.py -x -v --tb=short`
- **Per wave merge:** `pytest apps/backend/tests/test_graph.py -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `apps/backend/tests/test_graph.py` — all KNOW-04 tests
- [ ] `apps/backend/tests/conftest.py` — shared fixtures (sample JSON data)
- [ ] `apps/backend/tests/fixtures/` — subset of JSON files for unit testing
- [ ] Install networkx: `pip install networkx` — add to requirements.txt

### Validation Dimensions

| Dimension | How Measured | Pass/Fail Criteria |
|-----------|-------------|-------------------|
| Graph completeness | Count nodes by type after `build_graph()` | ≥59 champion, ≥30 trait, ≥45 item, ≥252 augment nodes |
| Edge correctness | Sample specific edges (Briar→Anima, Bloodthirster→B.F.Sword) | Edges exist with correct attributes |
| API responses | HTTP calls to `/api/graph/*` endpoints | 200 for valid entities, 404 with suggestions for invalid |
| Reload integrity | Reload graph, re-check counts | Same counts before/after reload |
| Performance | Time to first query after startup | <2 seconds for first query (graph builds lazily) |
| Test suite runtime | `pytest` duration | <5 seconds for full test suite |

---

## Security Domain

> Required when `security_enforcement` is enabled (absent = enabled). Omit only if explicitly `false` in config.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth on graph read endpoints (public TFT data) |
| V3 Session Management | no | No sessions in graph module |
| V4 Access Control | no | Graph is read-only; POST /reload is unauthenticated (ingest API has auth) |
| V5 Input Validation | yes | Entity name normalization + Pydantic query params |
| V6 Cryptography | no | No sensitive data in graph |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Large entity name causing DoS | Denial of Service | Limit `depth` (max 3), `limit` (max 50) in query params |
| Malformed entity name | Information Disclosure | Normalize all input; 404 with generic message (no stack traces) |
| Unbounded graph traversal | Denial of Service | NetworkX `single_source_shortest_path_length` with explicit `cutoff` parameter |

---

## Sources

### Primary (HIGH confidence)
- NetworkX 3.3 official docs — MultiDiGraph API, traversal algorithms
- Project codebase (`apps/backend/`) — existing FastAPI router patterns, Pydantic models, config.py
- Verified JSON data files — structure confirmed by reading first 100-150 lines of each

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions — all locked decisions explicitly stated
- REQUIREMENTS.md KNOW-01..04 — API contract from requirements doc

### Tertiary (LOW confidence)
- None — all critical claims verified from source files

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — NetworkX is the standard Python graph library; project patterns verified from existing code
- Architecture: HIGH — LazyGraphLoader pattern well-established; API design follows existing FastAPI conventions
- Pitfalls: HIGH — All pitfalls derived from actual data file structures and FastAPI behavior

**Research date:** 2026-04-23
**Valid until:** 2026-05-23 (30 days — NetworkX API is stable; project patterns unlikely to change)
