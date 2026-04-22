---
phase: "07"
name: "Polish & Smoke Test"
overall_score: 70
verdict: "NEEDS WORK"
critical_gap_count: 2
date: "2026-04-22"
dimensions_covered: 6/10
dimensions_partial: 3/10
dimensions_missing: 1/10
---

# EVAL-REVIEW — Phase 7: Polish & Smoke Test

**Audit Date:** 2026-04-22
**AI-SPEC Present:** No (polish/infra phase — decisions locked; no AI-SPEC.md generated)
**Overall Score:** 70/100
**Verdict:** NEEDS WORK — address critical gaps before production deployment

---

## Dimension Coverage

| # | Dimension | Status | Evidence | Finding |
|---|-----------|--------|----------|---------|
| 1 | **POLY-01: LRU Cache Implementation** | COVERED | `apps/backend/app/services/cache.py` (TTLCache, 500 entries, 1800s TTL); `apps/backend/app/services/retrieval.py` lines 29-41 (cache.get), line 77 (cache.set); config lines 59-60 verified | Cache correctly stores both embedding + chunks; cache key includes mode + patch; skips Ollama and SQL on hit |
| 2 | **POLY-03: Smoke Test — Script Created** | COVERED | `apps/backend/scripts/smoke_test.py` with 20 questions × 3 modes = 60 calls; `smoke_test_results.json` exists (all 60 failed due to backend not running, not code defect) | Script structurally correct; JSON output + exit code logic implemented |
| 3 | **POLY-04: GPU Monitoring — Backend Endpoint** | COVERED | `apps/backend/app/routes/gpu_status.py` with `GET /health/gpu`; registered in `main.py` lines 44, 47; graceful degradation on Ollama failure (lines 75-92) | Endpoint returns all 5 required fields; handles HTTP errors and exceptions |
| 4 | **POLY-04: GPU Monitoring — Frontend Badge** | COVERED | `useGpuStatus.ts` polls every 30s; `GpuBadge.tsx` color-codes (green/yellow/red); `App.tsx` line 6 imports, line 59 renders `<GpuStatusBadge />`; TypeScript build passed (1590 modules, 5.67s) | End-to-end path from Ollama `/api/ps` to browser badge is wired |
| 5 | **Cache Correctness (key isolation)** | COVERED | `_make_cache_key()` in `cache.py` line 22-25 uses `f"{mode}:{patch_part}:{query}"`; same query in different modes/patches produces different keys | Mode and patch are part of the cache key — correct isolation |
| 6 | **Cache Integration** | COVERED | `retrieval.py` line 7 imports `CacheEntry, embedding_cache`; line 29 checks `embedding_cache.get()` before line 44 `ollama.generate_embedding()`; line 77 calls `embedding_cache.set()` after hybrid search | Cache fully integrated at the right interception point in `retrieve_chunks()` |
| 7 | **GPU Endpoint Robustness** | COVERED | `gpu_status.py` lines 75-92 catch `HTTPStatusError` and generic `Exception`; return `GPUStatus(gpu_available=False, ...)` on any failure | Graceful degradation prevents 500 errors when Ollama is unavailable |
| 8 | **Smoke Test Completeness** | PARTIAL | 20 questions defined (5 comp, 5 item, 5 augment, 5 pivot); 3 modes tested per question = 60 total calls | Structure is complete, but **CRITICAL BUG**: smoke test hits wrong endpoint URLs (`/api/chat`, `/api/health/gpu`) — actual endpoints are `/chat` and `/health/gpu`. Script ran but all 60 calls returned HTTP 404. Test never actually exercised the backend |
| 9 | **Smoke Test CI-Readiness** | PARTIAL | JSON output (`smoke_test_results.json`) produced; exit code 0/1 implemented; structured `details` array per call | JSON output format is CI-compatible, but endpoint URL bug prevents actual CI usage |
| 10 | **Frontend Type Safety** | COVERED | `npm run build` succeeded: 1590 modules, 5.67s, no TypeScript errors | Build is clean |

**Coverage Score:** 6 COVERED, 3 PARTIAL, 1 MISSING → 6/10 COVERED → 60%

---

## Infrastructure Audit

| Component | Status | Finding |
|-----------|--------|---------|
| **Cache library** (`cachetools`) | Installed + Imported | `cachetools==5.5.0` in requirements.txt; imported in `cache.py` line 8 |
| **Eval tooling** | N/A for polish phase | No LLM judge or RAGAS evals — correct, this is infra not AI behavior eval |
| **Reference dataset** | N/A | No reference dataset — correct for smoke test approach |
| **CI/CD integration** | Missing | Smoke test is **NOT integrated into CI/CD** (per D-19: "Smoke test is NOT automated in CI — run manually before release") |
| **Online guardrails** | N/A | No guardrails defined for this phase — correct |
| **Tracing** | N/A | No tracing tool (Langfuse/Arize) — correct, this is polish not a new AI system |
| **GPU endpoint path correctness** | **BUG FOUND** | Smoke test uses `/api/health/gpu` but router has `prefix="/health"` → actual path is `/health/gpu` (no `/api` prefix) |
| **Chat endpoint path correctness** | **BUG FOUND** | Smoke test uses `/api/chat` but router has `prefix="/chat"` → actual path is `/chat` (no `/api` prefix) |

**Infrastructure Score:** 4 OK, 1 Missing, 2 Bug → effectively 2/7 = 29%

---

## Critical Gaps

### CRITICAL-1: Smoke Test Hits Wrong Endpoint URLs

**Severity:** Critical

The smoke test script hardcodes the `/api` prefix on both endpoints:

```18:36:apps/backend/scripts/smoke_test.py
CHAT_ENDPOINT = f"{BACKEND_BASE}/api/chat"
GPU_ENDPOINT = f"{BACKEND_BASE}/api/health/gpu"
```

But the routers are registered with these prefixes:

- `chat.router` has `prefix="/chat"` (no `/api`) → actual endpoint is `/chat`
- `gpu_status.router` has `prefix="/health"` (no `/api`) → actual endpoint is `/health/gpu`

The health router has no prefix at all (`APIRouter(tags=["health"])`), so its endpoints are `/health/*`.

**Effect:** All 60 smoke test calls returned HTTP 404. The `smoke_test_results.json` shows `"passed": 0, "failed": 60, "error": "HTTP 404"` — the test never successfully exercised a single chat call.

**Fix:** Update `smoke_test.py` lines 78-79:

```python
CHAT_ENDPOINT = f"{BACKEND_BASE}/chat"           # was: /api/chat
GPU_ENDPOINT = f"{BACKEND_BASE}/health/gpu"      # was: /api/health/gpu
```

After fixing, re-run: `cd apps/backend && python scripts/smoke_test.py`

### CRITICAL-2: Smoke Test Has Not Been Run Against a Live Backend

**Severity:** Critical

The smoke test was executed but returned 0/60 passed due to the endpoint bug above. Even after fixing the URLs, no successful smoke test run exists. This is a prerequisite for verifying the success criteria:
- "All 20 smoke test questions receive coherent, relevant answers without errors"
- "GPU memory stays under 16GB during normal operation"

**Fix:** After correcting the endpoint URLs (CRITICAL-1), run the smoke test against a running backend:

```bash
# Terminal 1: start backend
cd apps/backend
uvicorn app.main:app --reload

# Terminal 2: run smoke test
cd apps/backend
python scripts/smoke_test.py
```

Verify `smoke_test_results.json` shows `"passed": 60, "failed": 0`.

---

## Gaps & Remediation

### Must Fix Before Production

1. **[CRITICAL-1] Fix smoke test endpoint URLs** (`apps/backend/scripts/smoke_test.py`, lines 78-79)
   - Change `/api/chat` → `/chat`
   - Change `/api/health/gpu` → `/health/gpu`

2. **[CRITICAL-2] Run smoke test successfully** — execute against running backend, verify 60/60 pass

### Should Fix Soon

3. **[LOW] Verify cache hit latency < 50ms** — run a repeated query and time the response. Currently no automated timing test exists. Add to smoke test or create a small benchmark script:
   ```python
   import time
   start = time.perf_counter()
   chunks = await retrieve_chunks("Zeri carry items", "rag", "17.1")
   elapsed_ms = (time.perf_counter() - start) * 1000
   assert elapsed_ms < 50, f"Cache hit too slow: {elapsed_ms:.1f}ms"
   ```

4. **[LOW] Integrate smoke test into CI/CD** — per D-19 this was deferred, but for production reliability, consider adding `python scripts/smoke_test.py` to the deployment pipeline as a gate

### Nice to Have

5. **Manual GPU badge visual verification** — open `http://localhost:5173` and confirm the VRAM badge appears in the header (green/yellow/red based on usage)

6. **Manual cache verification** — repeat a RAG query within 30 minutes and confirm faster response (log timestamps or measure via browser network tab)

---

## Summary

Phase 7 delivered all three required features (cache, GPU monitoring, smoke test infrastructure) with high code quality. The implementation is well-structured and follows project conventions. However, the smoke test contains an endpoint URL bug that prevented it from ever successfully testing the backend. Fixing those two URLs and running the smoke test to completion are the only remaining blockers before the phase is fully verified.

**Files that need changes:**
- `apps/backend/scripts/smoke_test.py` — fix CHAT_ENDPOINT and GPU_ENDPOINT URL prefixes

**Files requiring manual verification after fix:**
- `apps/backend/scripts/smoke_test.py` — re-run to verify 60/60 pass
- Frontend at `http://localhost:5173` — confirm GPU badge renders
- Repeated query → measure cache hit latency < 50ms
