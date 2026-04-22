# Phase 5 Plan 03: TFT Static Data - DB Ingestion Summary

## Overview

**Phase:** 5
**Plan:** 03
**Subsystem:** TFT Data Ingestion
**Tags:** tft, db, embeddings, ingestion
**Dependency Graph:**
- Requires: Phase 5 Plan 02 (JSON Parsing)
- Provides: TFT chunks in DB with embeddings and metadata
- Affects: `scripts/ingest_tft_static.py`, `app/routes/ingest.py`

---

## One-Liner

Batch embed TFT chunks via Ollama and bulk insert with hash dedup into the chunks table; expose patch param and version check endpoint

---

## What Was Built

### Task 1: DB Insert Step in ingest_tft_static()

Updated `apps/backend/scripts/ingest_tft_static.py`:

**Added imports already present (from prior plans):**
- `from app.db import get_pool`
- `from app.services.ollama import ollama`
- `from app.utils.hashing import content_hash`

**Refactored `ingest_tft_static()` function:**
- Builds chunk list with type, text, hash, and metadata
- Handles empty chunk list (CDN unavailable) gracefully
- Batch embeds all chunks via `ollama.generate_embeddings(texts)` (batch size = 4)
- For each chunk: checks `SELECT 1 FROM chunks WHERE source = $1 AND content_hash = $2`
- Inserts with `ON CONFLICT (source, content_hash) DO NOTHING`
- Returns `{patch, status, ingested, skipped, total}` counts

**Key design points:**
- `source = f"tft_static:{type}:{patch}"` per D-07 (e.g. `tft_static:champions:17.1`)
- Hash dedup check BEFORE insert avoids duplicate rows on re-ingest
- Stats returned: ingested, skipped, total for observability
- No DELETE before INSERT — hash dedup handles re-ingest via skip logic

### Task 2: Updated /ingest/tft-static Endpoint

Updated `apps/backend/app/routes/ingest.py`:

**`POST /ingest/tft-static` changes:**
- Added `patch: str | None = None` query parameter
- FastAPI automatically treats as query param `?patch=17.1`
- Passes `patch=patch` to `ingest_tft_static()`

**New `GET /ingest/tft-static/version` endpoint:**
- Returns `{latest, cached, cache_dir, is_stale}`
- Used by Phase 6 automation to check if ingest is needed

---

## Key Decisions

| Decision | Rationale | Status |
|----------|-----------|--------|
| Batch embed size = 4 | One chunk per data type, VRAM-safe | Implemented |
| Hash dedup check before insert | Avoids duplicate rows on re-ingest | Implemented |
| ON CONFLICT DO NOTHING | Belt-and-suspenders alongside dedup check | Implemented |
| Stats return format | ingested/skipped/total for observability | Implemented |
| Version endpoint for automation | Phase 6 needs stale check before ingest | Implemented |

---

## Tech Stack

**Added/Modified:**
- `apps/backend/scripts/ingest_tft_static.py` - Refactored ingest_tft_static() with DB insert
- `apps/backend/app/routes/ingest.py` - Added patch param + version endpoint

**Patterns Used:**
- Async DB pool via `pool.acquire()` context manager
- Batch embedding via `ollama.generate_embeddings()`
- Hash deduplication via `content_hash()`
- Metadata JSONB with season/patch/type keys

---

## Key Files

| File | Action |
|------|--------|
| `apps/backend/scripts/ingest_tft_static.py` | Modified |
| `apps/backend/app/routes/ingest.py` | Modified |

---

## Deviations from Plan

None — plan executed exactly as written.

---

## Verification Results

### Task 1: Module Import
```
$ python -c "from scripts.ingest_tft_static import ingest_tft_static; print('Import OK')"
Import OK ✓
```

### Task 2: Route File Syntax
```
$ python -c "from app.routes.ingest import router; print('Routes:', [r.path for r in router.routes])"
Routes: ['/obsidian', '/tft-static', '/tft-static/version'] ✓
```

---

## Metrics

| Metric | Value |
|--------|-------|
| Duration | ~3 minutes |
| Tasks Completed | 2/2 |
| Files Modified | 2 |
| Commits | 2 |
| Lines Added | ~68 (net) |

---

## Self-Check: PASSED

- [x] `ingest_tft_static()` returns `{patch, status, ingested, skipped, total}`
- [x] Batch embedding calls `ollama.generate_embeddings()` with chunk texts
- [x] Hash dedup check before insert
- [x] `ON CONFLICT (source, content_hash) DO NOTHING`
- [x] `source = f"tft_static:{type}:{patch}"` format
- [x] `POST /tft-static` accepts `?patch=` param
- [x] `GET /tft-static/version` returns `{latest, cached, is_stale}`
- [x] Both commits exist

---

## Next Steps (Future Plans)

- Plan 05-04: Add CommunityDragon or other fallback CDN sources
- Phase 6: n8n scheduled ingest automation
- Phase 6: Wire TFT chunks into chat retrieval pipeline

---

*Generated: 2026-04-22*
*Phase: 05-tft-static-data*
*Status: Plan 03 complete*
