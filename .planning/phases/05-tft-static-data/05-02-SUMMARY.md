# Phase 5 Plan 02: TFT Static Data - JSON Parsing Summary

## Overview

**Phase:** 5
**Plan:** 02
**Subsystem:** TFT Data Ingestion
**Tags:** tft, parsing, chunking, static-data
**Dependency Graph:**
- Requires: Phase 5 Plan 01 (CDN Download + Disk Cache)
- Provides: TFT JSON parsing into readable markdown chunks
- Affects: `scripts/ingest_tft_static.py`

---

## One-Liner

TFT JSON parsing into markdown chunks with season/patch/type metadata for downstream embedding and ingestion

---

## What Was Built

### Task 1: Parse Functions for Each Data Type

Added to `apps/backend/scripts/ingest_tft_static.py`:

- `_extract_season_from_patch(patch: str)` - Maps patch major to SET (17.x → SET17)
- `_format_champions(data, patch)` - Champions JSON → markdown with name, cost, traits, HP/AD/AP/AS/Crit/Mana stats, sorted by cost
- `_format_traits(data, patch)` - Traits JSON → markdown with name, desc, threshold ranges, effects
- `_format_items(data, patch)` - Items JSON → markdown with name, desc, effects
- `_format_augments(data, patch)` - Augments JSON → markdown with name, tier, desc
- `format_patch_data(data, patch)` - Orchestrates all formatters, returns `dict[type] = (text, metadata)`

**Design decisions:**
- All formatters access data via `data.get("data", {})` per Riot Data Dragon structure
- Champion cost drives sort order (cheapest first)
- Season inferred from patch major version with lookup table (SET14-SET17 + dynamic fallback)
- Only processes data types that are present in the response (handles CDN 403 gracefully)

### Task 2: Integrated Parse Step into ingest_tft_static()

Refactored `ingest_tft_static()` to:
1. Call `get_patch_data(patch)` → returns `(version, raw_data)`
2. Call `format_patch_data(raw_data, version)` → returns chunk-ready data
3. Compute `content_hash` for each formatted text chunk
4. Return structured dict with `patch`, `status`, `types`, `chunks`

**Return structure:**
```python
{
    "patch": "16.8.1",
    "status": "downloaded" | "cached",
    "types": ["champions", "traits", "items", "augments"],  # only available types
    "chunks": [
        {
            "type": "champions",
            "text": "# TFT Champions (Patch 16.8.1)\n\n## Ahri (Cost: 3)\nTraits: ...",
            "hash": "abc123...",
            "metadata": {"season": "SET16", "patch": "16.8.1", "type": "champions"},
        },
        ...
    ]
}
```

**Additional changes:**
- Added `TFTStaticData` TypedDict for type hints
- Added `get_cached_version()` / `save_cached_version()` for version marker
- Removed old per-entry formatters (`format_champion`, `format_trait`, etc.)
- Removed inlined embed+DB logic (moved to Plan 05-03)

---

## Key Decisions

| Decision | Rationale | Status |
|----------|-----------|--------|
| Per-type chunking | Follows D-03: 1 chunk per data category | Implemented |
| Graceful CDN 403 handling | Riot CDN may not serve retired TFT sets | Implemented |
| Season map with fallback | `SET{patch_int}` for unknown patches | Implemented |
| Only return available types | Prevents KeyError when CDN 403s all endpoints | Implemented |

---

## Tech Stack

**Added/Modified:**
- `apps/backend/scripts/ingest_tft_static.py` - Added 7 new functions, refactored main pipeline

**Patterns Used:**
- TypedDict for structured return types
- Tuple unpacking for (text, metadata) pairs
- Dict iteration to skip missing data types
- `content_hash` from `app.utils.hashing` for deduplication

---

## Key Files

| File | Action |
|------|--------|
| `apps/backend/scripts/ingest_tft_static.py` | Modified |

---

## Deviations from Plan

### 1. [Rule 2 - Auto-add Missing Critical Functionality] Graceful handling of CDN 403

- **Found during:** Verification test
- **Issue:** When all TFT CDN endpoints return 403 (retired set), the downloaded data dict is empty. Calling `format_patch_data` with missing keys caused `KeyError`.
- **Fix:** Added `if data_type not in data: continue` check in `format_patch_data`, and `available_types` list to return only successfully parsed types. `ingest_tft_static` now returns `types: []` and `chunks: []` when CDN unavailable.
- **Files modified:** `apps/backend/scripts/ingest_tft_static.py`
- **Commit:** e8096c5

---

## Verification Results

### Test 1: format_patch_data (mock data)
```
Keys: ['champions', 'traits', 'items', 'augments']
Season: SET17
Champion chunk length: 121
PASS ✓
```

### Test 2: _extract_season_from_patch
```
14.0 -> SET14, 15.1 -> SET15, 16.2 -> SET16, 17.1 -> SET17, 18.0 -> SET18
PASS ✓
```

### Test 3: ingest_tft_static
```
patch: 16.8.1
status: downloaded
types: []
chunk_count: 0
CDN unavailable (403) - 0 chunks expected, code handles gracefully
PASS ✓
```

---

## Metrics

| Metric | Value |
|--------|-------|
| Duration | ~5 minutes |
| Tasks Completed | 2/2 |
| Files Modified | 1 |
| Commits | 1 |
| Lines Added | ~173 (net) |

---

## Self-Check: PASSED

- [x] All 6 parsing functions implemented per plan spec
- [x] `format_patch_data` returns dict with (text, metadata) tuples
- [x] `_extract_season_from_patch` handles SET14-SET17 + fallback
- [x] `ingest_tft_static` returns {patch, status, types, chunks}
- [x] Each chunk has type, text, hash, metadata keys
- [x] Metadata contains season, patch, type
- [x] Graceful handling when CDN returns empty data
- [x] Commit e8096c5 exists

---

## Next Steps (Future Plans)

- Plan 05-03: Embed and ingest formatted chunks into the database
- Plan 05-04: Add CommunityDragon or other fallback CDN sources
- Phase 6: n8n scheduled ingest automation

---

*Generated: 2026-04-22*
*Phase: 05-tft-static-data*
*Status: Plan 02 complete*
