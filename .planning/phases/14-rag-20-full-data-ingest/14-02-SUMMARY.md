---
phase: 14
plan: 02
subsystem: backend
tags: [ranking, retrieval, reranking, heuristics]

requires:
  - phase: 14-01
    provides: entity_type column, hybrid_search entity_filter
provides:
  - ranking_weights configuration
  - multi-factor heuristic reranking pipeline
affects: [14-01, 14-03]

tech-stack:
  added: []
  patterns: [multi-factor reranking, score boosting]

key-files:
  created: []
  modified:
    - apps/backend/app/config.py
    - apps/backend/app/services/ranking.py
    - apps/backend/app/services/retrieval.py

key-decisions:
  - "reranking applied in Python after SQL fetch — no SQL changes needed"
  - "score × patch_priority × entity_priority × recency_boost formula"

patterns-established:
  - "_ranking debug metadata attached to each chunk for observability"

requirements-completed: [RAG2-02]

duration: 8min
completed: 2026-04-23

---

# Phase 14: Plan 02 — Heuristic Reranking Summary

**Multi-factor reranking with patch_priority × entity_priority × recency_boost — prioritizes current patch champions/items**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-23T00:12:00Z
- **Completed:** 2026-04-23T00:20:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- ranking_weights dict added to Settings: patch_priority (17.1=1.0, 17.0=0.7, default=0.3), entity_priority (champion=1.2, item=1.1, augment=0.9, etc.), recency_boost (7d=1.2, 30d=1.0, default=0.8)
- get_patch_priority() helper function in config.py
- ranking.py rewritten: get_recency_boost(), get_entity_priority(), rerank_chunks()
- rerank_chunks() applies: score × patch_priority × entity_priority × recency_boost
- _ranking debug metadata attached to each chunk (cosine, patch_prio, entity_prio, recency, final_score)
- retrieve_chunks() already integrated in 14-01: calls rerank_chunks() after SQL fetch, before cache set

## Files Created/Modified

- `apps/backend/app/config.py` — ranking_weights dict + get_patch_priority() helper
- `apps/backend/app/services/ranking.py` — get_recency_boost(), get_entity_priority(), rerank_chunks()
- `apps/backend/app/services/retrieval.py` — integrated reranking (done in 14-01)

## Decisions Made

- reranking in Python after SQL fetch — avoids SQL complexity
- patch_priority: current patch 17.1=1.0, previous=0.7, older=0.3
- entity_priority: champion=1.2 (highest), item=1.1, trait=1.0, augment=0.9, system=0.8

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- reranking pipeline ready for streaming citations (14-03) — citations will reflect reranked scores
- All RAG queries now use heuristic reranking

---
*Phase: 14-rag-20-full-data-ingest*
*Completed: 2026-04-23*
