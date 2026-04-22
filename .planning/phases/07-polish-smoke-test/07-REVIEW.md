# Phase 7: Polish & Smoke Test — Code Review Report

**Reviewed:** 2026-04-22T00:00:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

---

## Summary

Reviewed all 6 Phase 7 source files: the TTL LRU cache backend, the GPU status route, the frontend `useGpuStatus` hook, the `GpuBadge` component, and the smoke test script.

Overall the code is well-structured. The TTL cache implementation is clean, the GPU status endpoint gracefully degrades, and the frontend components handle the null/unavailable states correctly. One **critical bug** was found: the smoke test script uses the wrong URL path for the GPU status endpoint, which will cause all GPU memory checks to silently return empty data in CI. Additionally, there is dead code in the smoke test's print helpers and a potential performance concern with unbounded cache keys in the retrieval service.

---

## Critical Issues

### CR-01: Smoke test uses wrong GPU endpoint path

**File:** `apps/backend/scripts/smoke_test.py:36`
**Severity:** Critical
**Description:** The `GPU_ENDPOINT` is set to `{BACKEND_BASE}/api/health/gpu`, but the `gpu_status` router registers itself with `prefix="/health"` (no `/api` prefix). The actual endpoint is `{BACKEND_BASE}/health/gpu`. This means every call to `get_gpu_status` in the smoke test will return a 404, and `gpu_before`/`gpu_after` will always be empty dicts — silently losing all GPU memory measurements.

**Fix:**
```python
# Before (wrong):
GPU_ENDPOINT = f"{BACKEND_BASE}/api/health/gpu"

# After (correct):
GPU_ENDPOINT = f"{BACKEND_BASE}/health/gpu"
```

---

## Warnings

### WR-01: Unused variables in smoke test print helpers

**File:** `apps/backend/scripts/smoke_test.py:210, 256`
**Severity:** Warning
**Description:** `status_str` is assigned but never read. On line 210, `status_str` is assigned the same value as `marker` but the latter is used in the output. On line 256, `status_str` is reassigned but the print statement on line 259 uses `marker` directly. These are dead stores indicating incomplete cleanup of an earlier iteration of the logic.

**Fix:**
```python
# Line 209-210: Remove the redundant assignment
# Before:
status_str = "PASS" if r.passed else "FAIL"
marker = "PASS" if r.passed else "FAIL"

# After:
marker = "PASS" if r.passed else "FAIL"

# Line 256: Remove the dead assignment
# Before:
marker = "PASS" if r.passed else "FAIL"
status_str = "PASS" if r.passed else "FAIL"

# After:
marker = "PASS" if r.passed else "FAIL"
```

### WR-02: Unbounded cache key size from query text

**File:** `apps/backend/app/services/retrieval.py:29, 47`
**Severity:** Warning
**Description:** The cache key in `_make_cache_key` (in `cache.py`) embeds the full query string directly: `f"{mode}:{patch_part}:{query}"`. There is no length validation on `query` before constructing the key. In the worst case, a very long query string (e.g., thousands of characters pasted by a user) would create an unnecessarily large key, consuming cache memory inefficiently and potentially causing issues with the underlying TTLCache hash table. The current 500-entry limit provides some protection, but a single huge key can still displace many smaller entries.

**Fix:**
```python
# In cache.py, add length validation in _make_cache_key or in EmbeddingCache.set:

MAX_QUERY_LENGTH = 512

def _make_cache_key(query: str, mode: str, patch: str | None) -> str:
    patch_part = patch if patch else "all"
    truncated_query = query[:MAX_QUERY_LENGTH] if len(query) > MAX_QUERY_LENGTH else query
    return f"{mode}:{patch_part}:{truncated_query}"
```

---

## Info

### IN-01: Silently swallowed errors in GPU status hook

**File:** `apps/frontend/src/hooks/useGpuStatus.ts:41-43`
**Severity:** Info
**Description:** The `refresh` callback uses an empty `catch` block that silently swallows all errors. While the fallback state (`gpu_available: false`) is reasonable, logging or surfacing persistent failures (e.g., via a toast or error counter) would aid debugging in production.

### IN-02: Missing `credentials` option in fetch

**File:** `apps/frontend/src/hooks/useGpuStatus.ts:15`
**Severity:** Info
**Description:** The `fetch` call does not include `credentials: "same-origin"` or similar. If the frontend is served from a different origin in some deployment configuration, cookies/auth tokens would not be sent. For the current smoke-test use case this is not a concern, but it is worth noting for future multi-origin deployments.

### IN-03: Smoke test result file written to cwd

**File:** `apps/backend/scripts/smoke_test.py:289`
**Severity:** Info
**Description:** The JSON results file is written to `"smoke_test_results.json"` in the current working directory. If the script is run from different directories (e.g., project root vs. `apps/backend/`), the output file ends up in different places. Consider using `__file__`-relative paths or an environment-variable-controlled output path:
```python
RESULTS_FILE = os.getenv("SMOKE_TEST_RESULTS", "smoke_test_results.json")
```

### IN-04: Type ignore comment in cache get

**File:** `apps/backend/app/services/cache.py:43`
**Severity:** Info
**Description:** The `# type: ignore[return-value]` suppresses a mypy/type-checker warning. The TTLCache returns `CacheEntry | None` but type inference may not track this correctly. This is a cosmetic issue; the code is correct at runtime.

---

## Findings Summary

| Category | Count |
|---|---|
| Critical | 1 |
| Warning | 2 |
| Info | 4 |
| **Total** | **7** |

---

_Reviewed: 2026-04-22_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
