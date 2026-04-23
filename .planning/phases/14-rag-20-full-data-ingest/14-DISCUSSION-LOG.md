# Phase 14: RAG 2.0 + Full Data Ingest - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-23
**Phase:** 14-rag-20-full-data-ingest
**Areas discussed:** Metadata Filtering, Reranking, Streaming Citations, Full Ingest Pipeline, Obsidian File Watcher

---

## Metadata Filtering

| Option | Description | Selected |
|--------|-------------|----------|
| Split functions | Split `hybrid_search_chunks_by_patch` into `hybrid_search_chunks($1...$5)` with entity_type param | |
| JSONB column + filter | Add `metadata entity_type text` column, filter via `WHERE metadata->>'entity_type' = 'champion'` | ✅ |

**User's choice:** JSONB column + SQL filter
**Notes:** Stronger — enables direct entity type queries in SQL without modifying function signatures

---

## Heuristic Reranking

| Option | Description | Selected |
|--------|-------------|----------|
| Python post-retrieval | Retrieve → rerank in Python code before returning. Clean, tunable | ✅ |
| SQL weighted scoring | Modify query with weighted scoring in SQL. Faster at query time, more complex | |

**User's choice:** Python post-retrieval
**Notes:** Cleaner separation of concerns; easier to tune reranking weights without schema changes

---

## Streaming Citations

| Option | Description | Selected |
|--------|-------------|----------|
| Progressive SSE | citation_start → tokens stream → citation_end. Users see citations appear gradually | |
| Batch at start | Emit all citations at response start, tokens stream after. Simple, good UX | |
| Hybrid progressive | Citations metadata at start + progressive reveal of citation content. Best UX, most complex | ✅ |

**User's choice:** Hybrid progressive
**Notes:** Citations metadata immediately visible → content revealed as it streams in. Best perceived performance.

---

## Full Ingest Pipeline

| Option | Description | Selected |
|--------|-------------|----------|
| Modular batch processors | Each data file has its own processor class. API endpoint. Clean, testable | ✅ |
| Unified ingest function | Single function handles all files with Pydantic validation. Fewer files | |
| CLI ingest script | Standalone Python script. Fast, no API needed | |

**User's choice:** Modular batch processors
**Notes:** Clear separation per data type. Each processor independently testable and maintainable.

---

## Obsidian File Watcher

| Option | Description | Selected |
|--------|-------------|----------|
| Include Phase 14 | Reactive sync is the finishing piece of RAG 2.0 | ✅ |
| Defer future phase | Focus on ingest + citations first | |

**User's choice:** Include Phase 14
**Notes:** File watcher completes the reactive RAG pipeline — reactive sync is essential for real-time vault integration.

---

## the agent's Discretion

- Exact chunk sizing per entity type (refine during implementation)
- Recency boost window (7 days initial value)
- File watcher debounce duration (500ms initial value)
- Citation progressive reveal animation (fade-in, skeleton → content)

---

## Deferred Ideas

None — discussion stayed within phase scope.
