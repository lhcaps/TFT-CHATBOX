# Phase 9: MetaTFT Real-time Intelligence — SPEC

**Gathered:** 2026-04-22
**Status:** PRD Express Path — requirements locked

<spec_lock>
## Requirements (locked via this SPEC)

**D-01:** NO browser automation (Selenium/Playwright). Use `httpx` to fetch pages. Parse JSON data embedded in page HTML using regex.

**D-02:** Data source: `https://www.metatft.com/comps` — extract all comp data (compositions, tiers, win rates, carries, items).

**D-03:** Transform scraped JSON into Markdown text chunks. Format: `"Theo MetaTFT hien tai, Dong hinh [Ten] dang o Tier [S/A/B] voi [X]% ti le Top 4. Tuong Carry la [Ten] can lap [items]..."`

**D-04:** Ingest MetaTFT chunks into existing `chunks` table with `source='metatft'` tag. Use same dedup pattern (source + content_hash UNIQUE).

**D-05:** New API endpoint: `POST /api/ingest/metatft` — runs Task D-01 + D-03, upserts chunks with `source='metatft'`.

**D-06:** Update existing n8n `patch_monitor.json` workflow: add a daily MetaTFT refresh node (12:00 noon every day) that calls `POST /api/ingest/metatft`.

**D-07:** Update LLM system prompt: when user asks about meta/comps, LLM should respond using retrieved MetaTFT data and format answer using Markdown with comp card syntax.

**D-08:** Frontend `CompCard` component: render LLM markdown output with comp card syntax into styled cards (tier badges, champion names, item lists with color coding).

**D-09:** Also ingest the full patch 17.1 and set overview data into RAG: from `https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/teamfight-tactics-patch-17-1/` and `https://teamfighttactics.leagueoflegends.com/en-us/set-overview/tft-set-17-space-gods/`.

</spec_lock>

## Phase Boundary

Deliver automated MetaTFT intelligence ingestion + frontend comp card display:
- Backend: `POST /api/ingest/metatft` endpoint — scrape MetaTFT, transform to Markdown, ingest into pgvector
- Automation: n8n workflow updated — daily MetaTFT refresh at 12:00 noon
- Frontend: `CompCard` component — renders comp data from LLM markdown
- Also: ingest full patch 17.1 + Space Gods set overview data into RAG

## In Scope

- `POST /api/ingest/metatft` endpoint (httpx + regex JSON extraction from metatft.com/comps)
- MetaTFT data → Markdown transformation (tier, winrate, carry, items per comp)
- Ingest into `chunks` table with `source='metatft'` tag
- n8n daily trigger for MetaTFT ingest (12:00 noon)
- `CompCard` frontend component with tier badges and item coloring
- Full patch 17.1 data ingestion (champion changes, items, augments, artifacts)
- Full Space Gods set overview ingestion (traits, gods, mechanics)

## Out of Scope

- MetaTFT API key (scrape public page, no auth needed)
- Real-time MetaTFT polling (daily is sufficient)
- Separate MetaTFT database table (reuse chunks table with source tag)
- MetaTFT comp comparison UI (beyond Markdown rendering)

## Acceptance Criteria

1. `POST /api/ingest/metatft` fetches `https://www.metatft.com/comps` via httpx, parses embedded JSON, transforms to Markdown, ingests into `chunks` table
2. n8n workflow fires daily at 12:00 noon calling `POST /api/ingest/metatft`
3. `CompCard` component renders comp markdown with tier badges (S=A, S=B, S=C with distinct colors)
4. LLM coach/RAG responses cite MetaTFT data with `[metatft]` source markers
5. Patch 17.1 full data + Space Gods set overview ingested into RAG

---

*Phase: 09-metatft-intelligence*
*SPEC gathered: 2026-04-22 via PRD Express Path*
