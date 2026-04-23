# Phase 11: TFT Knowledge Graph - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Build an in-memory directed multigraph using NetworkX from Set 17 verified data files. The graph enables cross-entity traversals: "best items for Briar?" → Briar node → item edges. The graph exposes FastAPI endpoints for structured queries and auto-reloads when patch data is ingested.

**Scope:**
- Node types: Champion, Item, Trait, Augment, God, System
- Edge types: HAS_TRAIT, BUILDS_FROM, ITEM_FOR_CHAMPION, SYNERGIZES, TRAIT_BREAKPOINT, GOD_ALIGNMENT
- Data sources: 7 verified JSON files in project root
- 4 plans covering: schema+model, API endpoints, auto-reload, unit tests
- Graph does NOT persist to disk — rebuilds from JSON on load

</domain>

<decisions>
## Implementation Decisions

### Data Source Priority (D-01)
- **deep_pack_v4_user_verified.json** — PRIMARY for champion data (highest detail, 59 champions, traits_numeric, ability summaries)
- **enhanced_pack.json** — secondary for Space Gods-specific data (9 gods with titles, focus areas)
- **data_pack.json** — fallback for missing champions or abilities
- **traits_full_user_verified.json** — primary for trait definitions
- **augments_full_user_verified.json** — 252 augments (Silver/Gold/Prismatic)
- **items_effects_expanded_set17.json** — item effects text and categories
- **items_formulas_full_set17.json** — item recipes (components)
- **rolling_odds_user_verified.json** — rolling odds by level

### Edge Construction Strategy (D-02)
- **Conservative approach** — only create edges that can be derived directly from verified data
- `HAS_TRAIT(champion, trait, count)` — from deep_pack_v4 champion's trait list
- `BUILDS_FROM(item, component_a, component_b)` — from items_formulas_full_set17.json
- `ITEM_FOR_CHAMPION(item, champion)` — from role/cost heuristics: carry champions → AD items, mage champions → AP items, tank champions → defensive items
- `SYNERGIZES(champion, champion)` — **NOT built** (no reliable meta data in current files)
- `COUNTERS(champion, champion)` — **NOT built** (no matchup data available)
- `TRAIT_BREAKPOINT(trait, count, bonus)` — from traits_full_user_verified.json tiers{}
- `GOD_ALIGNMENT(god, trait)` — **NOT built** (no god↔trait links in current files)
- `ITEM_INTO(item, upgraded_item)` — **NOT built** (no upgrade chains in current files)

### Trait Classification (D-03)
- Extract origin/class distinction from `deep_pack_v4_user_verified.json` → `traits_numeric.origins` vs `traits_numeric.classes`
- `traits_full_user_verified.json` does NOT distinguish origin/class — use deep_pack_v4 as the source of truth
- If a trait appears in deep_pack_v4 as `origins.*` → type = "origin"
- If a trait appears in `classes.*` → type = "class"
- Some traits may appear in both — classify as "origin" by default

### Partial Data Handling (D-04)
- Include items with `completeness: "partial"` in the graph
- Add `is_verified: bool` attribute to every node
- Nodes with `is_verified: false` are still queryable but flagged in API responses
- Augment nodes: all are treated as `is_verified: true` (verified from user data)

### Graph Loading Strategy (D-05)
- **Lazy-load** — graph builds on first API query, not on backend startup
- Add `LazyGraphLoader` class that defers JSON parsing + NetworkX construction
- Startup is NOT blocked by graph loading
- No disk serialization — rebuild from JSON each time (JSON parsing is fast, serialization adds complexity)
- `POST /api/graph/ingest` reloads graph by re-parsing all JSON files

### API Integration Points (D-06)
- Graph module lives in `backend/graph/` directory
- Importable from `backend.graph.knowledge_graph` as a singleton
- FastAPI router in `backend/routers/graph.py`
- LLM chat pipeline (Phase 13) will call graph queries via HTTP to these endpoints

### the agent's Discretion
- Exact heuristics for ITEM_FOR_CHAMPION (how to determine "carry" vs "tank" from cost/traits)
- Champion role detection: infer from traits (e.g., "Anima" → HP-focused) and cost (5-cost → usually carry)
- How to handle champion names with special characters or spaces (normalize to lowercase IDs)
- Exact format of `neighbors` response — whether to include edge weights or just node names

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning
- `.planning/ROADMAP.md` — Phase 11 goal, scope, edge types, node types, plan list
- `.planning/REQUIREMENTS.md` — KNOW-01..04 acceptance criteria
- `.planning/STATE.md` — current project state, knowledge graph decisions locked
- `.planning/PROJECT.md` — project vision, stack summary

### Data Files (in project root)
- `augments_full_user_verified.json` — 252 augments: `{name, tier, description}` — AugmentNode source
- `traits_full_user_verified.json` — 30+ traits: `{champions[], text, tiers{}}` — TraitNode source
- `items_effects_expanded_set17.json` — item effects: `{name, effect, stats, completeness}` — ItemNode source (effects)
- `items_formulas_full_set17.json` — item recipes: `{name, recipe[]}` — BUILDS_FROM edge source
- `tft_set17_patch17_1_deep_pack_v4_user_verified.json` — champions + traits_numeric — ChampionNode + TraitNode primary source
- `tft_set17_patch17_1_enhanced_pack.json` — Space Gods systems — GodNode + SystemNode source
- `tft_set17_patch17_1_data_pack.json` — champion roster baseline — fallback for missing data
- `rolling_odds_user_verified.json` — rolling odds by level — SystemNode source
- `tft_set17_patch17_1_enhanced_report.md` — data quality notes and ingest strategy

### Backend Codebase
- `backend/app.py` — FastAPI app structure
- `backend/routers/` — existing router patterns
- `backend/models.py` — Pydantic models for API responses
- `backend/services/ingest.py` — existing ingest pipeline patterns
- Phase 5 plans: `.planning/phases/05-tft-static-data/05-*-PLAN.md` — data loading patterns

### Prior Phase Context
- `.planning/phases/04-rag-foundation/04-CONTEXT.md` — RAG pipeline patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/services/` — existing service layer pattern for data loading
- `backend/models.py` — Pydantic BaseModel for API schemas
- `backend/routers/*.py` — FastAPI router pattern with prefix, tags
- `backend/config.py` — settings management

### Established Patterns
- JSON files loaded via `Path(__file__).parent.parent / "filename.json"` relative path pattern
- Async-first with `@asynccontextmanager` for startup/shutdown
- Logging with `logging.getLogger(__name__)`
- Bearer token auth via `security.py` dependency

### Integration Points
- `backend/app.py` → include router: `app.include_router(graph_router, prefix="/api/graph")`
- Phase 13 chat pipeline will call `GET /api/graph/neighbors/{entity}` for entity queries
- Ingest pipeline (`backend/services/ingest.py`) will emit events that trigger graph reload

</code_context>

<specifics>
## Specific Ideas

- Champion node IDs: lowercase normalized (e.g., "Briar", "Soraka" → "briar", "soraka")
- Trait node IDs: same normalized approach
- Item node IDs: full name normalized (e.g., "Bloodthirster" → "bloodthirster")
- Augment node IDs: full name (e.g., "AFK", "Anima Commander")
- God node IDs: full name (e.g., "soraka_god" to avoid collision with champion "soraka")
- System node IDs: snake_case (e.g., "rolling_odds", "realm_of_the_gods")
- Graph singleton: `knowledge_graph = LazyGraphLoader()` — accessed via `knowledge_graph.get()`
- NetworkX graph type: `nx.MultiDiGraph` for multi-edges between same node pair

</specifics>

<deferred>
## Deferred Ideas

### Build Later from Meta Data
- `SYNERGIZES(champion, champion)` — no reliable source data currently
- `COUNTERS(champion, champion)` — no matchup data in current files
- `GOD_ALIGNMENT(god, trait)` — no god↔trait links in enhanced_pack.json
- `ITEM_INTO(item, upgraded_item)` — no upgrade chain data in current files

### Future Phase Candidates
- **Phase 13 (Smart Chat Engine)** — SYNERGIZES could be built from LLM-generated synergy suggestions
- **Phase 14 (RAG 2.0)** — GOD_ALIGNMENT could be extracted from RAG chunk analysis
- These are explicitly NOT in Phase 11 scope

</deferred>

---

*Phase: 11-tft-knowledge-graph*
*Context gathered: 2026-04-23*
