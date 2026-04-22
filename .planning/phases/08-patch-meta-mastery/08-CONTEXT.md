# Phase 8: Patch Meta Mastery - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver automated TFT patch intelligence: backend persists patch state in DB, n8n monitors Riot for new patches, auto-ingests both static data and patch notes when a new patch drops, and frontend shows patch version + staleness with manual check button.

Scope:
- DB schema: `patch_info` table (current_patch, latest_available, last_checked, last_ingested, patch_notes_url)
- Backend: `GET /api/patch/status`, `POST /api/ingest/patch-notes`
- n8n: activate patch_monitor workflow, add patch notes ingest, verbose Discord notifications
- Frontend: patch version badge + "Check for updates" button

Out of scope:
- Scheduling ingest runs manually (n8n handles auto-scheduling)
- Multi-patch version support (only track current + latest)
- Push notifications (Discord webhook only)

</domain>

<decisions>
## Implementation Decisions

### Patch state storage
- **D-01:** DB table `patch_info` as single source of truth (not file-based `latest_version.txt`)
- **D-02:** Table columns: `current_patch`, `latest_available`, `last_checked`, `last_ingested`, `patch_notes_url`, `ingest_status`
- **D-03:** Existing `GET /api/patch/current` refactored to read from DB instead of file

### Patch notes ingestion API
- **D-04:** New dedicated endpoint `POST /api/ingest/patch-notes` — n8n calls this after static data ingest completes
- **D-05:** Endpoint accepts `?patch=X.Y` param; if omitted, uses latest_available from DB
- **D-06:** Scrapes Riot patch page using BeautifulSoup, chunks content, generates embeddings, ingests into `chunks` table
- **D-07:** Same hash-based deduplication as existing ingest (source + content_hash UNIQUE)
- **D-08:** Existing `scrape_patch17.py` refactored into a reusable function called by the API endpoint

### n8n workflow
- **D-09:** Activate `patch_monitor.json` workflow (currently `active: false`)
- **D-10:** After triggering `/api/ingest/tft-static`, ALSO trigger `/api/ingest/patch-notes` with same patch version
- **D-11:** Discord notification: TWO messages — "New patch X.Y detected, ingesting..." AND "Ingest complete: X new chunks / Y skipped"
- **D-12:** Discord on FAIL: include error message + patch version

### Frontend patch display
- **D-13:** Patch version badge in header/chat area: "Patch 17.1" with color coding
- **D-14:** Staleness state: "Up to date" (green), "Stale — X.Y available" (yellow), "Checking..." (gray spinner)
- **D-15:** "Check for updates" button — calls `GET /api/patch/status`, shows result, does NOT auto-ingest (user must know ingest is running)
- **D-16:** Ingest triggered only by n8n (automated), not by frontend button

### Patch URL discovery
- **D-17:** Scrape listing page `https://teamfighttactics.leagueoflegends.com/en-us/news/` to find patch article URLs dynamically
- **D-18:** Pattern match on URL: `/teamfight-tactics-patch-{X}-{Y}/` — extract version from URL
- **D-19:** Fallback: URL pattern `riot.com/news/...patch-{major}-{minor}/` if listing page is inaccessible

### Error handling
- **D-20:** On scrape failure: log error, skip patch notes (don't fail the whole workflow), Discord notifies
- **D-21:** On CDN 403 for static data: use CommunityDragon fallback (existing behavior preserved)

### the agent's Discretion
- Exact DB column types and indexes
- Frontend badge styling (colors, positioning, animation)
- How "Check for updates" refreshes the staleness UI (optimistic update vs. wait for response)
- n8n workflow node arrangement and naming
- BeautifulSoup selector strategy for Riot page structure

</decisions>

<specifics>
## Specific Ideas

- "I want to see 'Patch 17.2 available!' in the UI — clear and visible"
- "When I click 'Check for updates', show me whether it's stale before running ingest"
- "Discord should tell me both when ingest started and when it finished"
- Patch notes scrape should use same chunking strategy as Obsidian ingest (2000-char chunks, 500 overlap)

</specifics>

<canonical_refs>
## Canonical References

### Backend API
- `apps/backend/app/routes/patch_state.py` — Existing patch state endpoint (to be refactored)
- `apps/backend/app/routes/ingest.py` — Existing ingest endpoints (reference pattern for new endpoint)
- `apps/backend/scripts/scrape_patch17.py` — Existing patch scraper (reusable logic to extract)
- `apps/backend/app/db.py` — Database connection pool (asyncpg)

### Database
- `supabase/migrations/0001_initial_schema.sql` — Existing schema (new `patch_info` table follows same patterns)
- `supabase/migrations/0003_hybrid_search_tft_patch.sql` — Existing metadata indexing patterns

### n8n
- `n8n/workflows/patch_monitor.json` — Existing workflow to activate and extend
- `n8n/workflows/credentials.json` — Existing credential configuration

### Frontend
- `apps/frontend/src/App.tsx` — Existing app structure (add patch status component)
- `apps/frontend/src/App.tsx` §header/chat — Where to place patch version badge

### Project planning
- `.planning/ROADMAP.md` — Phase 8 requirements (PATCH-01 through PATCH-05)
- `.planning/STATE.md` — Gap analysis for v1.1

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scrape_patch_notes()` in `scrape_patch17.py` — BeautifulSoup scraping, works for any patch URL
- `ingest_into_db()` in `scrape_patch17.py` — embedding + DB insert with deduplication
- `format_as_markdown()` in `scrape_patch17.py` — chunk formatting with season/patch metadata
- `get_latest_version()` in `ingest_tft_static.py` — fetches from Riot CDN versions.json
- `asyncpg` connection pool from `app/db.py` — used throughout backend for DB operations

### Established Patterns
- All backend routes use `Depends(verify_api_key)` for auth (ingest endpoints)
- Session/message repositories use raw asyncpg (no ORM)
- Frontend uses React state + fetch for API calls
- Dark mode Tailwind classes throughout

### Integration Points
- New `patch_info` table joins with existing `chunks` table (patch metadata in chunks.metadata)
- `POST /api/ingest/patch-notes` follows same pattern as existing `POST /api/ingest/obsidian`
- `GET /api/patch/status` replaces/refactors existing `GET /api/patch/current`
- n8n `patch_monitor` workflow connects to both new endpoints

</code_context>

<deferred>
## Deferred Ideas

- Auto-ingest on button click (not just check) — add to backlog as PATCH-06
- Multiple patch version support (keep history of past patches) — future phase
- Browser notifications for new patch — future phase

</deferred>

---

*Phase: 08-patch-meta-mastery*
*Context gathered: 2026-04-22*
