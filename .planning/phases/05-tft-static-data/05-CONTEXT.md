# Phase 5: TFT Static Data - Context

**Gathered:** 2026-04-22 (auto mode — recommended defaults applied)
**Status:** Ready for planning

<domain>
## Phase Boundary

Ingest champions, traits, items, and augments from Riot Data Dragon (ddragon) and CommunityDragon CDN into the `chunks` table with season and patch metadata. Enable scoped retrieval by patch version via SQL `WHERE` filtering on `metadata->>'patch'`. Disk cache avoids re-downloading unchanged patch data. Static TFT JSON on-disk cache already noted in POLY-02 requirements.

**Scope:** `POST /api/ingest/tft-static` endpoint, download logic (Riot CDN + CommunityDragon), per-type chunking (4 chunks: champions/traits/items/augments), per-patch disk cache, metadata JSONB storage (season, patch, data_type), metadata-filtered `hybrid_search_chunks` variant.
**Out of scope:** Per-unit chunking (Phase v2), streaming chunk reveal (Phase v2), n8n scheduled ingest (Phase 6), GPU monitoring (Phase 7).

</domain>

<decisions>
## Implementation Decisions

### Data Sources (D-01 to D-02)
- **D-01:** Download from Riot Data Dragon CDN (`ddragon`) and CommunityDragon CDN (`gitcdn.one`) — official, stable, no API keys required.
- **D-02:** Version check via Riot's `versions.json` (CDN: `https://ddragon.leagueoflegends.com/cdn/versions.json`) — HTTP HEAD request, compare with cached version before downloading.

### Chunking Strategy (D-03 to D-04)
- **D-03:** Per-type chunking: 1 chunk per data category (champions, traits, items, augments). Total ~4 chunks per patch. Chunk size targets ~2000 chars; larger types split as needed.
- **D-04:** Each chunk formatted as readable markdown-like text (see D-07 specifics). Heading metadata stores full Riot API path.

### Disk Cache (D-05 to D-06)
- **D-05:** Per-patch folder cache at `~/.tft-copilot/cache/{patch}/` — e.g., `~/.tft-copilot/cache/17.1/`. Enables rollback to older patches and avoids re-downloading unchanged data.
- **D-06:** On ingest: check if `~/.tft-copilot/cache/{patch}/` exists → if yes, read from disk → if no, download from CDN → save to cache. Version comparison only requires fetching `versions.json` (small HEAD request).

### Metadata Storage (D-07 to D-09)
- **D-07:** Each chunk stored with `metadata = {"season": "SET17", "patch": "17.1", "type": "champions"|"traits"|"items"|"augments"}`. `source` field = `tft_static:{type}:{patch}`.
- **D-08:** Content text format: Riot JSON normalized to readable text. Example: champion = `# {name}\nCost: {cost}\nTraits: {traits}\nStats: {...}`, item = `# {name}\nEffects: {effects}`, augment = `# {name}\nTier: {tier}\nDesc: {desc}`.
- **D-09:** Hash deduplication: `content_hash` on the formatted text (same pattern as Obsidian ingest). If hash unchanged, skip insert.

### Metadata Filtering (D-10 to D-11)
- **D-10:** SQL `WHERE metadata->>'patch' = $patch` added to `hybrid_search_chunks` call in `retrieval.py` — patch-specific retrieval without polluting query embedding.
- **D-11:** Route accepts optional `?patch=17.1` query param; if omitted, falls back to latest patch (most recent `source` by name order).

### Ingest Endpoint (D-12)
- **D-12:** `POST /api/ingest/tft-static` already stubbed in `app/routes/ingest.py`. Update to call the full ingest pipeline: version check → cache check → download → parse → chunk → embed → insert.

### Claude's Discretion
- Exact CDN URLs (verified via web search for current Riot CDN structure)
- Number of chunks per type (if >2000 chars, split into 2)
- Whether to use `ON CONFLICT` or `DELETE + INSERT` for re-ingest (same hash-dedup approach as Obsidian is fine)
- Batch embedding size (follows existing BATCH_SIZE=16 pattern)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project context
- `.planning/PROJECT.md` — Vision, stack, constraints, TFT policy compliance
- `.planning/REQUIREMENTS.md` — RAG-05, RAG-06, POLY-02 requirements
- `.planning/ROADMAP.md` — Phase 5 goal, success criteria, dependencies
- `.planning/STATE.md` — Accumulated context, locked decisions from Phase 1-4

### Prior phase context
- `.planning/phases/02-backend-core/02-CONTEXT.md` — Backend decisions (SSE format, mode system, history window)
- `.planning/phases/03-frontend-chat/03-CONTEXT.md` — Frontend decisions (SSE parsing, session state, hook architecture)
- `.planning/phases/04-rag-foundation/04-CONTEXT.md` — RAG decisions (hybrid search, citation format, batch embedding, metadata JSONB pattern)

### Existing code (read before implementing)
- `apps/backend/scripts/ingest_tft_static.py` — Stub to replace with full implementation (download + cache + parse + chunk + embed + insert)
- `apps/backend/scripts/patch_refresh.py` — `TFT_PATCH_CACHE` path pattern to follow for disk cache
- `apps/backend/app/routes/ingest.py` — `POST /ingest/tft-static` stub endpoint
- `apps/backend/app/services/retrieval.py` — `retrieve_chunks()` to add optional patch filter
- `apps/backend/app/services/ollama.py` — `generate_embeddings()` batch embed (reused)
- `apps/backend/scripts/ingest_obsidian.py` — Reference for chunking, embedding, dedup patterns
- `supabase/migrations/0001_initial_schema.sql` — `chunks` table + `hybrid_search_chunks` function (extend with patch filter)
- `apps/backend/app/config.py` — Settings pattern for new config values

### Research findings
- `.planning/research/STACK.md` — Ollama batch embedding API, `dimensions: 1024`, cache patterns
- `.planning/research/ARCHITECTURE.md` — Ingestion pipeline architecture, chunking strategy, incremental update pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/ingest_obsidian.py` — chunking pattern (split_with_heading), batch embed call, hash dedup, `stats` dict return — all reusable
- `scripts/patch_refresh.py` — `TFT_PATCH_CACHE` path (`Path.home() / ".tft-copilot" / "patch_cache.json"`) → extend to per-patch folder cache
- `app/routes/ingest.py` — `POST /ingest/tft-static` route already exists, just needs full implementation
- `app/services/retrieval.py` — `retrieve_chunks()` accepts `top_k`, add optional `patch` param
- `app/services/ollama.py` — `generate_embeddings()` (batch) already implemented, reuse for TFT chunks
- `app/config.py` — add `tft_cache_dir: str = "~/.tft-copilot/cache"`

### Established Patterns
- Hash deduplication: `content_hash()` from `app.utils.hashing`, stored in `content_hash` column, check before insert
- Batch embedding: 16 chunks per request via `ollama.generate_embeddings()`
- Metadata JSONB: store structured metadata, query via `metadata->>'key'`
- Async DB: `pool.acquire()` context manager pattern throughout
- SSE events: `event: {name}\ndata: {json}\n\n` format

### Integration Points
- Ingest route (`/ingest/tft-static`) → `ingest_tft_static.py` (updated)
- `ingest_tft_static.py` → `ollama.generate_embeddings()` (batch embed)
- `ingest_tft_static.py` → DB `chunks` table (bulk insert)
- `retrieval.py` → `hybrid_search_chunks` (add patch WHERE clause)
- Chat route → retrieval with patch filter (patch from query param or session metadata)

</code_context>

<specifics>
## Specific Ideas

- CDN base URLs: `https://ddragon.leagueoflegends.com/cdn/` + version + `/data/en_US/tft/` (champions, items, traits) and `https://gitcdn.one/github/CommunityDragon/...` for augments
- Version check: `GET https://ddragon.leagueoflegends.com/cdn/versions.json` → parse first entry → compare with `~/.tft-copilot/cache/latest_version.txt`
- Cache folder: `~/.tft-copilot/cache/{patch}/` with subfolders `champions.json`, `items.json`, `traits.json`, `augments.json`
- Content format example (champion): `# Ahri\nCost: 3\nTraits: Cultist, Spirit\nStats: HP: 750 | AD: 65 | AP: 70 | AS: 0.75 | Crit: 25% | Mana: 0/60`
- Content format example (augment): `# Portable Forge\nTier: 3 (Prismatic)\nDesc: Your champions can hold an additional item. They gain 30 bonus Armor and Magic Resist.`
- `source` field format: `tft_static:champions:17.1`, `tft_static:augments:17.1`
- Metadata: `{"season": "SET17", "patch": "17.1", "type": "champions"}`
- Patch filter SQL: `WHERE metadata->>'patch' = $patch` appended to hybrid search
- Route: `POST /ingest/tft-static?patch=17.1` (optional, defaults to latest)

</specifics>

<deferred>
## Deferred Ideas

### Ideas for Future Phases
- Per-unit chunking (each champion/item/augment = separate chunk) — Phase v2 for more granular retrieval
- TFT patch auto-detection via Riot API webhooks (instead of manual trigger) — Phase 6 automation
- Heuristic reranking by patch/season priority — Phase v2
- TFT data in Coach mode: retrieval-augmented coach responses grounded in actual champion stats — Phase 5 integration with Phase 4 retrieval

### Not in Scope
- Real-time data or game state — Phase 1-4 already locked
- WebSocket or alternative streaming — SSE sufficient
- Redis or distributed cache — in-memory LRU sufficient (Phase 7)
- Auth/user management — single local user

</deferred>

---

*Phase: 05-tft-static-data*
*Context gathered: 2026-04-22*
*Status: Ready for planning*
