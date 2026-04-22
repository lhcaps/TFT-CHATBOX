# Phase 7: Polish & Smoke Test - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 07-polish-smoke-test
**Areas discussed:** Caching Strategy, GPU Monitoring Approach, Smoke Test Format

---

## Caching Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Redis distributed cache | External Redis, multi-worker safe | |
| In-process LRU (cachetools) | Single-process, fast, no extra dependency | ✓ |
| functools.lru_cache on generate_embedding | Simplest, but caches embeddings only, not chunks | |

**User's choice:** In-process LRU with TTL
**Notes:** MVP scale doesn't warrant Redis. `functools.lru_cache` doesn't support TTL — cachetools TTLCache is the right choice.

---

## GPU Monitoring Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Ollama /api/ps polled by frontend directly | No backend change, CORS issue likely | |
| Backend /health/gpu endpoint + frontend polls | Clean separation, FastAPI route | ✓ |
| SSE stream of GPU updates | Over-engineered for this use case | |

**User's choice:** Backend `/health/gpu` endpoint with periodic polling
**Notes:** Frontend polls every 30 seconds while chat is active, or on-demand.

---

## Smoke Test Format

| Option | Description | Selected |
|--------|-------------|----------|
| Automated pytest suite | Requires test infra setup | |
| Standalone smoke_test.py script | Single file, httpx + asyncio, manual run | ✓ |
| n8n smoke test workflow | Overcomplicated for this | |

**User's choice:** Standalone `apps/backend/scripts/smoke_test.py`
**Notes:** Manual run before release. Not in CI for MVP.

---

## Deferred Ideas

- Redis-based cache — v2 / Phase 8+
- CI smoke test — v2 / Phase 8+
- Retrieval quality metrics (recall@K) — EVAL-02
- Structured logging — EVAL-03

