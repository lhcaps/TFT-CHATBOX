---
phase: 06-automation
plan: "06-01"
subsystem: backend
tags: [automation, auth, backend]
key-files:
  created:
    - apps/backend/app/middleware/auth.py
    - apps/backend/app/routes/patch_state.py
  modified:
    - apps/backend/app/routes/ingest.py
    - apps/backend/app/config.py
    - apps/backend/app/main.py
metrics:
  endpoints_added: 1
  endpoints_protected: 2
---

## Summary

Built backend infrastructure for n8n automation integration with Bearer token authentication. The auth middleware validates Bearer tokens on ingest write endpoints while exposing a public GET endpoint for n8n to check current patch state.

### What was built

1. **Auth middleware** (`apps/backend/app/middleware/auth.py`): `verify_api_key` FastAPI Depends function that validates Bearer tokens against `API_SECRET_KEY` env var, returning 401 for invalid/missing tokens and 500 if the server secret is not configured.

2. **Patch state endpoint** (`apps/backend/app/routes/patch_state.py`): `GET /api/patch/current` returns the cached TFT version from `latest_version.txt`, used by n8n workflows to determine if re-ingestion is needed.

3. **Protected ingest endpoints** (`apps/backend/app/routes/ingest.py`): Both `POST /ingest/obsidian` and `POST /ingest/tft-static` now require Bearer auth; `GET /ingest/tft-static/version` remains public (read-only).

4. **API secret setting** (`apps/backend/app/config.py`): `api_secret_key` field auto-loaded from `API_SECRET_KEY` env var.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | d9cac37 | Add Bearer token auth middleware |
| Task 2 | 1f07734* | Add GET /api/patch/current endpoint |
| Task 3 | 01f37c9 | Add Bearer auth to ingest write endpoints |
| Task 4 | f0740f8 | Add api_secret_key setting for Bearer auth |

*Task 2 was completed in phase 06-02 as part of the API_SECRET_KEY infrastructure work.

## Deviations

**Task 2 already completed (06-02):** The patch_state endpoint and router registration in main.py were already implemented in phase 06-02. No changes needed for this task.

## Verification Results

```
grep "verify_api_key" apps/backend/app/middleware/auth.py
# Found: async def verify_api_key(authorization: str = Header(...)) -> str:

grep "router = APIRouter" apps/backend/app/routes/patch_state.py
# Found: router = APIRouter(prefix="/patch", tags=["patch"])

grep "latest_version.txt" apps/backend/app/routes/patch_state.py
# Found: marker = Path(settings.tft_cache_dir) / "latest_version.txt"

grep "patch_state.router" apps/backend/app/main.py
# Found: app.include_router(patch_state.router)

grep "Depends(verify_api_key)" apps/backend/app/routes/ingest.py
# Found: 2 occurrences (ingest_obsidian, ingest_tft_static_route)

grep "api_secret_key" apps/backend/app/config.py
# Found: api_secret_key: str = ""
```

## Self-Check: PASSED

All success criteria verified:
- [x] `apps/backend/app/middleware/auth.py` exists with `verify_api_key` dependency
- [x] `apps/backend/app/routes/patch_state.py` exists with `GET /api/patch/current`
- [x] `apps/backend/app/routes/ingest.py` — write endpoints protected, read endpoint public
- [x] `apps/backend/app/config.py` — `api_secret_key` setting present
- [x] `apps/backend/app/main.py` — `patch_state.router` registered
