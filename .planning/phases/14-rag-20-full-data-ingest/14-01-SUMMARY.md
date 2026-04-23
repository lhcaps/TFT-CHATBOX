---
phase: 14
plan: 01
subsystem: database
tags: [postgres, pgvector, hybrid-search, rag, metadata]

requires:
provides:
  - entity_type JSONB column for document_chunks
  - hybrid_search_chunks_by_patch SQL function with 5th entity_filter param
  - entity_filter parameter in retrieve_chunks() and ChatRequest
affects: [14-02, 14-04, 14-05]

tech-stack:
  added: []
  patterns: [SQL generated column, JSONB metadata filtering, cache key extension]

key-files:
  created: []
  modified:
    - apps/backend/app/services/retrieval.py
    - apps/backend/app/services/cache.py
    - apps/backend/app/models.py
    - apps/backend/app/routes/chat.py
    - apps/frontend/src/api/types.ts

key-decisions:
  - "entity_type as GENERATED ALWAYS STORED column from JSONB metadata — no schema migration needed for existing rows"
  - "Cache key extended to include entity_filter for proper cache segregation"

patterns-established:
  - "SQL migration embedded in _ensure_schema() for idempotent startup"

requirements-completed: [RAG2-01]

duration: 12min
completed: 2026-04-23

---

# Phase 14: Plan 01 — Metadata Filtering Summary

**entity_type JSONB column + hybrid_search with 5th entity_filter parameter — enables targeted RAG queries by entity type**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-23T00:00:00Z
- **Completed:** 2026-04-23T00:12:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- entity_type GENERATED column added to document_chunks (from JSONB metadata)
- idx_chunks_entity_type index created for fast entity filtering
- hybrid_search_chunks_by_patch SQL function replaced with enhanced version supporting entity_filter 5th param
- retrieve_chunks() accepts entity_filter parameter and passes to SQL
- Embedding cache key extended to include entity_filter for proper cache segregation
- ChatRequest model extended with entity_filter field
- Frontend ChatOptions type extended with entityFilter field

## Files Created/Modified

- `apps/backend/app/services/retrieval.py` — _ensure_schema() migration + enhanced hybrid_search + entity_filter in retrieve_chunks()
- `apps/backend/app/services/cache.py` — cache key extended with entity_filter
- `apps/backend/app/models.py` — ChatRequest.entity_filter field added
- `apps/backend/app/routes/chat.py` — build_messages() + stream_ollama_tokens() pass entity_filter
- `apps/frontend/src/api/types.ts` — ChatOptions.entityFilter field added

## Decisions Made

- Used GENERATED ALWAYS AS (metadata->>'entity_type') STORED — no migration needed for existing rows
- Cache key extended from 3 to 4 params (mode:patch:query → mode:patch:entity:query)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- entity_type column and hybrid_search entity_filter ready for 14-02 (reranking calls retrieve_chunks which now supports entity_filter)
- Streaming citations (14-03) and ingest (14-04) can now leverage entity filtering

---
*Phase: 14-rag-20-full-data-ingest*
*Completed: 2026-04-23*
