# Phase 7: Polish & Smoke Test - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

System achieves production-readiness through three concrete deliverables:
1. Query embedding LRU cache with 30-minute TTL (< 50ms on cache hit)
2. GPU/VRAM monitoring visible in frontend via Ollama /api/ps
3. 20-question smoke test suite covering comp/item/augment/pivot scenarios

Phase 6 n8n automation must remain intact — no breaking changes.

</domain>

<decisions>
## Implementation Decisions

### Caching: LRU Implementation

- **D-01:** Use `cachetools` LRU (or `functools.lru_cache` + dict) — lightweight, no extra dependency
- **D-02:** Key = `(query_text, mode, patch)` — mode normal/rag/coach determines system prompt, patch determines TFT static data filter
- **D-03:** TTL = 30 minutes (1800s), enforced on lookup (not just on write)
- **D-04:** Cache stores `(embedding_vector, retrieved_chunks)` — avoids re-running SQL hybrid_search on cache hit
- **D-05:** Target < 50ms on cache hit — verified by timing the full `retrieve_chunks()` call including cache lookup
- **D-06:** Cache lives in-process (per-worker) — acceptable for MVP since backend is single-worker (uvicorn)
- **D-07:** Cache invalidation: never invalidates early (TTL is sufficient for MVP)

### GPU Monitoring: Data Source

- **D-08:** Poll `GET http://localhost:11434/api/ps` — returns loaded models + memory breakdown per device
- **D-09:** Parse `ps_response["memory"]["used"]` and `["memory"]["total"]` for VRAM fraction
- **D-10:** Backend exposes `GET /health/gpu` endpoint returning `{gpu_available, vram_used_mb, vram_total_mb, models_loaded}`
- **D-11:** Frontend polls `GET /health/gpu` every 30 seconds while chat is active, or on-demand on button press
- **D-12:** Display: `GPU: 5212 / 16384 MB (32%)` or `GPU: N/A` if Ollama doesn't report GPU info
- **D-13:** Place GPU status in ChatShell header or a collapsible status bar — not intrusive, always visible

### Smoke Test: Scope & Format

- **D-14:** Script: `apps/backend/scripts/smoke_test.py` — standalone, no external deps beyond httpx + asyncio
- **D-15:** 20 questions across 4 categories (5 per category):
  - Comp: "What are the best comps for patch 17.1?"
  - Item: "What items do I slam on Zeri carry?"
  - Augment: "Best first augment for a fast 8 roll down strategy?"
  - Pivot: "I got 2-star Yone and 2-star Kayn — which should I commit to?"
- **D-16:** Each question tests exactly one mode: runs in Normal, RAG, and Coach modes
- **D-17:** Success = all 20 questions return HTTP 200, no exception, response has > 10 tokens
- **D-18:** Output: pass/fail per question, summary table, estimated time
- **D-19:** Smoke test is NOT automated in CI — run manually before release
- **D-20:** Smoke test verifies GPU memory < 16GB after test run

### Windows Path Handling (POLY-05 carry-over)

- **D-21:** All file paths use `pathlib.Path` — no raw strings with forward slashes
- **D-22:** `~/.tft-copilot/` resolved via `Path.home() / ".tft-copilot"` on all platforms
- **D-23:** CRLF handled in `ingest_obsidian.py` — open files with `encoding="utf-8"` not `"r"`

### Integration Constraints

- **D-24:** Phase 6 n8n Bearer auth remains intact — no changes to `apps/backend/app/middleware/auth.py` or `apps/backend/app/routes/ingest.py`
- **D-25:** Chat streaming must not be affected by cache layer — cache operates on `retrieve_chunks()`, not on chat response streaming
- **D-26:** GPU endpoint `/health/gpu` must not break existing `/health` endpoint — separate route, no modification to `routes/health.py`

### Agent's Discretion

- Exact LRU size limit (e.g., max 500 entries)
- Frontend VRAM display styling (progress bar vs text vs icon)
- Smoke test question wording (keep intent, adjust phrasing)
- How to surface GPU status to user (header badge, collapsible panel, tooltip)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Backend Architecture
- `apps/backend/app/services/ollama.py` — OllamaService for embedding generation
- `apps/backend/app/services/retrieval.py` — retrieve_chunks() (where cache wraps)
- `apps/backend/app/routes/chat.py` — chat streaming (must not break)
- `apps/backend/app/routes/health.py` — existing /health endpoint pattern

### Frontend
- `apps/frontend/src/hooks/useStreamingMessages.ts` — active streaming hook
- `apps/frontend/src/components/ChatShell.tsx` — main layout
- `apps/frontend/src/api/chat.ts` — API client patterns

### Automation (Phase 6 — no breaking changes)
- `apps/backend/app/middleware/auth.py` — Bearer auth (intact)
- `apps/backend/app/routes/ingest.py` — protected endpoints (intact)
- `n8n/workflows/patch_monitor.json` — n8n workflow (intact)

### Research
- `.planning/research/ARCHITECTURE.md` — overall component breakdown
- `.planning/research/STACK.md` — stack decisions

### Smoke Test
- `.planning/REQUIREMENTS.md` § POLY-03 — 20-question eval spec

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/backend/app/services/ollama.py`: `OllamaService.generate_embeddings()` already batch-embeds — the cache should wrap `generate_embedding()` (single query) in `retrieval.py`, not the batch endpoint
- `apps/backend/app/routes/health.py`: Pattern for creating a new `/health/gpu` route — similar structure, same file
- `apps/frontend/src/api/chat.ts`: Pattern for making authenticated API calls from frontend — reuse for `/health/gpu` polling
- `apps/frontend/src/components/ui/card.tsx`: Existing UI card component — reuse for GPU status display

### Established Patterns
- FastAPI `Depends()` pattern: new `/health/gpu` route follows same pattern as existing `/health`
- Async in-process state: `CHAT_HISTORY_WINDOW` and `rag_top_k` already live in `config.py` — embedding cache TTL goes there too
- SSE streaming: chat route uses SSE `data:` format — GPU status should be REST polling, not SSE (simpler, doesn't interfere with chat stream)

### Integration Points
- Cache intercepts `retrieve_chunks()` in `retrieval.py` — before `ollama.generate_embedding()` call
- GPU status: new route in `routes/health.py` or new file `routes/gpu_status.py`, registered in `main.py`
- Frontend: new `useHealth` hook + GPU badge in `ChatShell.tsx` header

</code_context>

<specifics>
## Specific Ideas

- Cache hit should be so fast (< 50ms) that RAG mode feels instant for repeated queries
- GPU display should be subtle — not a prominent dashboard widget, just a small status indicator
- Smoke test questions should be specific enough to distinguish Normal vs RAG vs Coach mode outputs
- Smoke test should test the three modes separately for the SAME question to validate mode switching works

</specifics>

<deferred>
## Deferred Ideas

- Redis-based distributed cache for multi-worker deployment — Phase 8+
- Automated smoke test in CI pipeline — Phase 8+
- Retrieval quality metrics (recall@K) — EVAL-02 in v2
- Structured logging per request — EVAL-03 in v2

</deferred>

---

*Phase: 07-polish-smoke-test*
*Context gathered: 2026-04-22*
