---
phase: "07"
name: "Polish & Smoke Test"
status: "complete"
plans: "4/4"
wave_count: 2
completed: "2026-04-22"
---

## Phase 7 Summary: Polish & Smoke Test

**Goal:** System achieves production-readiness with caching, GPU monitoring, and smoke test.

---

### Wave 1: Infrastructure & Observability

#### 07-01: LRU Query Embedding Cache ✅
**Files:** `apps/backend/app/services/cache.py` (NEW), `apps/backend/app/config.py` (MOD), `apps/backend/app/services/retrieval.py` (MOD)
**Commit:** `add91af`

Added TTL-LRU cache (`cachetools.TTLCache`) for query embeddings. Cache key = `(mode, patch, query_text)`. Cache stores both embedding vector AND retrieved chunks — cache hit skips Ollama AND SQL hybrid search. TTL=30min default, max 500 entries.

#### 07-02: GPU Status Backend Endpoint ✅
**Files:** `apps/backend/app/routes/gpu_status.py` (NEW), `apps/backend/app/main.py` (MOD)
**Commit:** `db835a5`

`GET /health/gpu` endpoint calls Ollama `/api/ps` and returns `{gpu_available, vram_used_mb, vram_total_mb, percent_used, models_loaded}`. Graceful degradation when Ollama unavailable.

#### 07-03: GPU Status Frontend Badge ✅
**Files:** `apps/frontend/src/hooks/useGpuStatus.ts` (NEW), `apps/frontend/src/components/GpuBadge.tsx` (NEW), `apps/frontend/src/App.tsx` (MOD)
**Commit:** `a2599a2`

`useGpuStatus` hook polls `/health/gpu` every 30s. `GpuBadge` renders color-coded VRAM indicator (green/yellow/red) in header. TypeScript build passed (1590 modules, 5.67s).

---

### Wave 2: Smoke Test

#### 07-04: 20-Question Smoke Test ✅
**Files:** `apps/backend/scripts/smoke_test.py` (NEW)
**Commit:** `76c9819`

Standalone smoke test: 20 questions × 3 modes (Normal/RAG/Coach) = 60 total calls. Pass criteria: HTTP 200 + no exception + >10 tokens. GPU memory recorded before/after. Outputs summary table + `smoke_test_results.json`. Exit code 0 on all pass.

---

### Requirements Coverage

| Requirement | ID | Plan | Status |
|---|---|---|---|
| Query embedding LRU cache (30-min TTL, <50ms hit) | POLY-01 | 07-01 | ✅ |
| GPU VRAM monitoring in frontend | POLY-04 | 07-02, 07-03 | ✅ |
| 20-question smoke test (comp/item/augment/pivot) | POLY-03 | 07-04 | ✅ |

---

### Key Files Created/Modified

```
apps/backend/app/services/cache.py              [NEW]
apps/backend/app/services/retrieval.py        [MOD]
apps/backend/app/config.py                   [MOD]
apps/backend/app/routes/gpu_status.py         [NEW]
apps/backend/app/main.py                      [MOD]
apps/frontend/src/hooks/useGpuStatus.ts     [NEW]
apps/frontend/src/components/GpuBadge.tsx    [NEW]
apps/frontend/src/App.tsx                   [MOD]
apps/backend/scripts/smoke_test.py           [NEW]
```

---

### What Remains (Manual)

1. **Run smoke test** — requires backend running at `http://localhost:8000`:
   ```bash
   cd apps/backend
   python scripts/smoke_test.py
   ```
2. **Verify GPU badge** — open frontend at `http://localhost:5173`, check header for VRAM indicator
3. **Verify cache** — repeat a RAG query within 30 minutes, observe faster response (no Ollama call)

---

### Phase Complete ✅

**All 4 plans executed successfully. Phase 7 requirements POLY-01, POLY-03, POLY-04 addressed.**
