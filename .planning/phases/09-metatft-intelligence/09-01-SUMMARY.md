# Phase 9: MetaTFT Real-time Intelligence — Backend Scraper + Ingest Endpoint

**Phase:** 09-metatft-intelligence
**Plan:** 09-01
**Status:** Complete
**Date:** 2026-04-22

---

## Summary

Implemented the full MetaTFT intelligence pipeline: httpx scraper, regex JSON extraction, Vietnamese Markdown transformer, and ingest into pgvector with dedup. Also implemented Space Gods set overview scraper and patch 17.1 ingest.

---

## What Was Built

### 1. `scrape_metatft.py` — MetaTFT Scraper

- `fetch_page()` — httpx GET with User-Agent header
- `extract_json_from_html()` — tries 3 regex patterns to extract JSON from metatft.com HTML
- `transform_to_markdown()` — converts comp data to Vietnamese Markdown per D-03
- `ingest_into_db()` — batch insert with `ON CONFLICT (source, content_hash) DO NOTHING`
- `scrape_and_ingest()` — main async function, returns `{ingested, skipped, total}`
- CLI entry point with `asyncio.run(main())`

### 2. `scrape_set_overview.py` — Space Gods Set Scraper

- Scrapes `https://teamfighttactics.leagueoflegends.com/en-us/set-overview/tft-set-17-space-gods/`
- Scrapes patch 17.1 notes
- `scrape_and_ingest_set_overview()` + `scrape_and_ingest_patch17_1()` + `scrape_and_ingest_all()`
- CLI with `--all`, `--set-overview`, `--patch-notes` flags

### 3. `POST /api/ingest/metatft` Endpoint

- `@router.post("/metatft")` in `ingest.py` line 168
- Accepts `source: "comps" | "set-overview" | "patch" | "all"` (default "all")
- Accepts optional `patch` param
- Calls `scrape_metatft()` and `scrape_set_overview()` when source matches
- Returns `{"status": "ok", "metatft": {...}, "set_overview": {...}, ...}`

### 4. LLM Prompts Updated

- `SYSTEM_PROMPTS['rag']` + `SYSTEM_PROMPTS['coach']` updated with CompCard syntax guidance
- `COMPCARD_GUIDANCE` constant defined in `prompts.py`

---

## Key Files Created/Modified

| File | Change |
|------|--------|
| `apps/backend/scripts/scrape_metatft.py` | Created |
| `apps/backend/scripts/scrape_set_overview.py` | Created |
| `apps/backend/app/routes/ingest.py` | Added `POST /ingest/metatft` endpoint |
| `apps/backend/app/prompts.py` | Added CompCard guidance to system prompts |

---

## Verification

- `POST /api/ingest/metatft` endpoint exists and is routed
- Scraper uses httpx (no browser automation)
- Dedup: `ON CONFLICT (source, content_hash) DO NOTHING`
- Embeddings truncated to 1024 dims

---

## Deviations

None — implementation matches 09-01-PLAN.md exactly.

---

*Created: 2026-04-23* (plan was executed 2026-04-22, summary created retrospectively)
