# Phase 9: MetaTFT Real-time Intelligence - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning
**Source:** PRD Express Path (.planning/phases/09-metatft-intelligence/09-SPEC.md)

<domain>
## Phase Boundary

Deliver automated MetaTFT intelligence ingestion + frontend comp card display:
- Backend: `POST /api/ingest/metatft` endpoint — scrape MetaTFT, transform to Markdown, ingest into pgvector
- Automation: n8n workflow updated — daily MetaTFT refresh at 12:00 noon
- Frontend: `CompCard` component — renders comp data from LLM markdown
- Also: ingest full patch 17.1 + Space Gods set overview data into RAG
</domain>

<decisions>
## Implementation Decisions

### Scraping
- **D-01** — NO browser automation (Selenium/Playwright). Use `httpx` to fetch pages. Parse JSON data embedded in page HTML using regex.
- **D-02** — Data source: `https://www.metatft.com/comps` — extract all comp data (compositions, tiers, win rates, carries, items).
- **D-03** — Transform scraped JSON into Markdown text chunks. Format: `"Theo MetaTFT hien tai, Dong hinh [Ten] dang o Tier [S/A/B] voi [X]% ti le Top 4. Tuong Carry la [Ten] can lap [items]..."`

### Backend Ingest
- **D-04** — Ingest MetaTFT chunks into existing `chunks` table with `source='metatft'` tag. Use same dedup pattern (source + content_hash UNIQUE).
- **D-05** — New API endpoint: `POST /api/ingest/metatft` — runs scrape + transform + ingest with `source='metatft'`.
- **D-07** — Update LLM system prompt: when user asks about meta/comps, LLM should respond using retrieved MetaTFT data and format answer using Markdown with comp card syntax.

### Additional Ingest
- **D-09** — Also ingest the full patch 17.1 and set overview data into RAG:
  - `https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/teamfight-tactics-patch-17-1/`
  - `https://teamfighttactics.leagueoflegends.com/en-us/set-overview/tft-set-17-space-gods/`

### Automation
- **D-06** — Update existing n8n `patch_monitor.json` workflow: add a daily MetaTFT refresh node (12:00 noon every day) that calls `POST /api/ingest/metatft`.

### Frontend
- **D-08** — Frontend `CompCard` component: render LLM markdown output with comp card syntax into styled cards (tier badges, champion names, item lists with color coding).

### Requirements Mapping
- **META-01** → D-01 + D-02 + D-03 + D-04 + D-05 (scraper endpoint)
- **META-02** → D-03 (MetaTFT data transformer)
- **META-03** → D-09 (additional ingest)
- **META-04** → D-06 (n8n daily trigger)
- **META-05** → D-08 (CompCard frontend)

### the agent's Discretion
- Exact regex patterns for extracting JSON from MetaTFT HTML (not specified)
- Whether to create a new scraper script (`scrape_metatft.py`) or extend existing `scrape_patch17.py`
- CompCard rendering approach (CSS-only vs component library)
- How to parse Space Gods set overview page (same `scrape_patch17.py` patterns reusable)
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Ingest Patterns
- `apps/backend/app/routes/ingest.py` — existing ingest endpoint pattern (POST /ingest/patch-notes)
- `apps/backend/scripts/scrape_patch17.py` — existing scraper (httpx + BeautifulSoup, reusable patterns: scrape_patch_url, scrape_patch_notes, format_as_markdown, ingest_into_db)
- `apps/backend/app/db.py` — asyncpg connection pool (get_pool)
- `apps/backend/app/services/ollama.py` — embedding generation (ollama.generate_embeddings)
- `apps/backend/app/utils/hashing.py` — content_hash for dedup

### n8n Workflow
- `n8n/workflows/patch_monitor.json` — existing workflow to extend with daily MetaTFT trigger

### Frontend
- `apps/frontend/src/App.tsx` — existing app structure (header with GpuStatusBadge, PatchStatus)
- `apps/frontend/src/components/PatchStatus.tsx` — existing status component to follow as pattern

### Backend Prompt
- `apps/backend/app/prompts.py` — existing prompt definitions (for D-07: update system prompt)

### DB Schema
- Existing `chunks` table with `source` + `content_hash` UNIQUE constraint (from v1.0)
- Existing `patch_info` table (from v1.1 Phase 8)

</canonical_refs>

<specifics>
## Specific Ideas

### MetaTFT JSON Extraction
MetaTFT embeds comp data as JSON in `<script>` tags in the page HTML. The D-01 constraint (no browser automation) means using `httpx` + `re.findall(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})', html)` style regex to extract the embedded state.

### Vietnamese Markdown Transform (D-03)
Example output format:
```
Theo MetaTFT hien tai, Dong hinh **Katarina** dang o Tier **S** voi **52%** ti le Top 4.
Tuong Carry la **Katarina** voi **items**: Qujin, Giant Slayer, Bloodthirster.
Cac tuong phu: Zedd, Ekko, Riven, Fiora.
Traits: **Duelist**, **Arcane**.
```

### n8n Extension (D-06)
Add a new Cron node firing at 12:00 (noon) that calls `POST /api/ingest/metatft`. Can branch from existing workflow or be a separate parallel workflow. Discord notification on success/failure.

### CompCard Syntax
LLM outputs Markdown with a specific syntax for comp cards. The frontend `CompCard` component parses this and renders styled cards:
```markdown
### Comp: Katarina Duelist
**Tier:** S | **Top4:** 52% | **Avg Place:** 2.1
**Carry:** Katarina
**Items:** [QSS] [GS] [BT]
**Units:** Zedd, Ekko, Riven, Fiora
**Traits:** Duelist 6, Arcane 3
```
```

### Multiple Data Sources (D-09)
1. Patch 17.1: `scrape_patch17.py` already handles this URL pattern
2. Space Gods set overview: New URL pattern needs a `scrape_set_overview()` function

</specifics>

<deferred>
## Deferred Ideas

None — SPEC covers phase scope fully.

</deferred>

---

*Phase: 09-metatft-intelligence*
*Context gathered: 2026-04-22 via PRD Express Path*
