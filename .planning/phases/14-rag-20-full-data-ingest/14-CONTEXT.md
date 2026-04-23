# Phase 14: RAG 2.0 + Full Data Ingest - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Enhance the retrieval pipeline with metadata filtering by entity type, streaming citations with progressive reveal, heuristic reranking by patch/season priority, and ingest all Set 17 verified data into the vector DB. Replace the flat 32-chunk ingest with a rich, structured corpus of 252 augments + 59 champions + 45+ items + traits + systems + rolling odds → 500+ high-quality chunks.

**Scope:**
- Metadata filtering: add entity_type JSONB column + enhanced hybrid_search function with entity type filter
- Heuristic reranking: patch_priority × entity_priority × recency_boost before RRF
- Streaming citations: progressive reveal (citations metadata at start + content revealed as retrieved)
- Full ingest pipeline: 7 data files → modular batch processors → 500+ chunks
- Obsidian file watcher for real-time reactive sync

**Out of scope:**
- Model upgrade (MODEL-01)
- Cross-session memory (SESS-04)
- Retrieval debug panel (RAG-10)

</domain>

<decisions>
## Implementation Decisions

### Metadata Filtering (D-01)
- **JSONB entity_type column:** Add `metadata entity_type text` column to chunks table
- **Filter in SQL:** `WHERE metadata->>'entity_type' = 'champion'`
- **Enhanced hybrid_search:** `hybrid_search_chunks($1, $2, $3, $4, $5)` where $5 is optional entity_type filter
- **Entity types:** champion, item, trait, augment, system

### Heuristic Reranking (D-02)
- **Python post-retrieval reranking:** Retrieve from DB → rerank in Python code before returning
- **Formula:** `score × patch_priority × entity_priority × recency_boost`
  - `patch_priority`: current patch (17.1) = 1.0, previous patch (16.8.1) = 0.7, older = 0.3
  - `entity_priority`: champion > item > trait > augment > system (for meta questions)
  - `recency_boost`: 1.2x for chunks ingested in last 7 days
- **RRF fusion:** Final merge using Reciprocal Rank Fusion after reranking

### Streaming Citations (D-03)
- **Hybrid progressive reveal:**
  1. Citations metadata emitted at response start (all citations, no content yet)
  2. Tokens stream progressively
  3. Citation content revealed incrementally as retrieved
  4. citation_end event at response end with full text
- **SSE events:**
  - `citation_start`: opens streaming source indicator with citation metadata
  - Citation content revealed progressively
  - `citation_end`: finalizes with full citation text + score
- **Frontend behavior:** Citations panel shows skeleton/loading state → fills in as content arrives

### Full Ingest Pipeline (D-04)
- **Modular batch processors:** Each data file has its own processor class
  - `AugmentProcessor` → augments_full_user_verified.json (252 augments)
  - `ChampionProcessor` → tft_set17_patch17_1_deep_pack_v4_user_verified.json (59 champions)
  - `ItemProcessor` → items_effects_expanded_set17.json (45+ items)
  - `TraitProcessor` → traits_full_user_verified.json (30+ traits)
  - `SystemProcessor` → tft_set17_patch17_1_enhanced_pack.json (9 Space Gods)
  - `RollingOddsProcessor` → rolling_odds_user_verified.json
  - `DataPackProcessor` → tft_set17_patch17_1_data_pack.json
- **API endpoint:** `POST /api/ingest/batch` — accepts processor type, calls appropriate processor
- **Chunk sizing:** champions × 400 chars, items × 300 chars, augments × 200-500 chars, traits × 300 chars
- **Target:** 500+ high-quality chunks with entity_type metadata

### Obsidian File Watcher (D-05)
- **Include in Phase 14:** Reactive sync is the finishing piece of RAG 2.0
- **Approach:** File system watcher (e.g., watchdog) that triggers re-embed + re-ingest on vault file changes
- **API endpoint:** `POST /api/ingest/reactive` — called by watcher on file change
- **Debouncing:** Wait for file system to settle (500ms debounce) before triggering ingest

### the agent's Discretion
- Exact chunk sizing per entity type (refine during implementation)
- Recency boost window (7 days is the initial value)
- File watcher debounce duration (500ms initial value)
- Citation progressive reveal animation (fade-in, skeleton → content)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning
- `.planning/ROADMAP.md` — Phase 14 goal, scope, RAG2-01..05, traceability
- `.planning/STATE.md` — current project state, Phase 11-13 complete, Phase 14 in progress
- `.planning/PROJECT.md` — project vision, stack summary, locked decisions
- `.planning/REQUIREMENTS.md` — RAG2-01..05 acceptance criteria

### Prior Phase Context
- `.planning/phases/11-tft-knowledge-graph/11-CONTEXT.md` — graph endpoints, node/edge types, lazy-load strategy
- `.planning/phases/12-ui-ux-redesign/12-CONTEXT.md` — UI decisions, cosmic theme, overflow fix
- `.planning/phases/13-smart-chat-engine/13-CONTEXT.md` — entity JSON markers, query routing, card design

### Backend Codebase
- `apps/backend/app/services/retrieval.py` — existing `retrieve_chunks()` and `hybrid_search_chunks_by_patch()` functions
- `apps/backend/app/routes/chat.py` — chat endpoint, `stream_ollama_tokens()`, SSE event format, citation handling
- `apps/backend/app/config.py` — settings management
- `apps/backend/app/db.py` — database pool and connection management

### Frontend Codebase
- `apps/frontend/src/components/MessageList.tsx` — citation rendering, streaming dots, citation filter
- `apps/frontend/src/components/CitationCard.tsx` — citation card display (expandable on click)
- `apps/frontend/src/components/CitationModal.tsx` — citation modal (full-text view)
- `apps/frontend/src/api/types.ts` — Citation, Message, SSEEvent types

### Data Files (Verified)
- `augments_full_user_verified.json` — 252 augments (Silver/Gold/Prismatic)
- `tft_set17_patch17_1_deep_pack_v4_user_verified.json` — 59 champions + traits + systems
- `items_effects_expanded_set17.json` — 45+ items with effect text
- `traits_full_user_verified.json` — 30+ traits with champions + breakpoints
- `tft_set17_patch17_1_enhanced_pack.json` — 9 Space Gods + Realm of the Gods
- `tft_set17_patch17_1_data_pack.json` — full champion roster + abilities + meta
- `rolling_odds_user_verified.json` — rolling odds by level (verified)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/backend/app/services/retrieval.py` — existing hybrid search functions that need enhancement
- `apps/backend/app/routes/chat.py` — existing SSE event format (token/done/citation/error) — new citation_start/citation_end extend this
- `MessageList.tsx` — existing CitationCard rendering with click-to-expand — already supports progressive loading states
- `CitationCard.tsx` — already has truncation + expand behavior
- Existing data files all in project root

### Established Patterns
- SSE event format: `event: {type}\ndata: {json}\n\n`
- Citation object: `{id, source, heading, text, score}`
- Streaming dots: animated bounce (purple-400)
- Backend: FastAPI, httpx async, PostgreSQL with pgvector

### Integration Points
- `apps/backend/app/services/retrieval.py`: Add entity_type parameter to `hybrid_search_chunks_by_patch`
- `apps/backend/app/routes/chat.py`: Add citation_start/citation_end events to `stream_ollama_tokens`
- `apps/backend/app/routes/ingest.py` (or new): Add batch ingest endpoint with processor selection
- `apps/frontend/src/components/MessageList.tsx`: Update citation rendering to handle progressive reveal
- `apps/frontend/src/components/CitationCard.tsx`: Support loading/skeleton state

</code_context>

<specifics>
## Specific Ideas

### Chunk Size Targets
```
augments: 200-500 chars per chunk → ~200 chunks
traits: 300 chars per chunk → ~60 chunks
items: 300 chars per chunk → ~80 chunks
champions: 400 chars per chunk → ~120 chunks
systems/rolling odds: 200 chars per chunk → ~40 chunks
Total: ~500+ chunks
```

### SSE Citation Events
```python
# Citation metadata at response start
yield f"event: citation\ndata: {json.dumps({'citation': citation_data})}\n\n"

# OR new citation_start event for progressive reveal
yield f"event: citation_start\ndata: {json.dumps({'id': cid, 'source': src, 'heading': hdr})}\n\n"
yield f"event: citation_content\ndata: {json.dumps({'id': cid, 'text': txt, 'score': scr})}\n\n"
yield f"event: citation_end\ndata: {json.dumps({'id': cid, 'done': True})}\n\n"
```

### Ingest API Design
```python
@router.post("/ingest/batch")
async def ingest_batch(processor: str, file_path: str | None = None):
    # processor: "augment" | "champion" | "item" | "trait" | "system" | "rolling_odds"
    # If file_path is None, uses default path for that processor type
```

</specifics>

<deferred>
## Deferred Ideas

### Future Phase Candidates
- **v2 (MODEL-01)** — Model upgrade to qwen3:8b or gemma3:12b for better Coach reasoning
- **v2 (SESS-03)** — Session export as Markdown to Obsidian
- **v2 (SESS-04)** — Cross-session memory
- **v2 (EVAL-01..03)** — Eval/observability suite

### Out of Scope for Phase 14
- Model upgrade (MODEL-01)
- Cross-session memory (SESS-04)
- Retrieval debug panel (RAG-10)

</deferred>

---

*Phase: 14-rag-20-full-data-ingest*
*Context gathered: 2026-04-23*
