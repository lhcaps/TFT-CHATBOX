# Milestones

## v1.4 Smart & Polished — PLANNED 2026-04-23

**Date:** 2026-04-23
**Phases:** 4 (11–14)
**Goal:** Transform TFT Local Copilot into a smart, interconnected knowledge system with a polished UI.

### Four Pillars

1. **Phase 11: Knowledge Graph** — NetworkX in-memory graph with Champion/Item/Trait/Augment/God/System nodes and edges. Enables cross-entity traversals and structured queries.
2. **Phase 12: UI/UX Core Redesign** — Fix message overflow, CitationCard expansion, CompCard Tailwind migration, responsive breakpoints, loading state polish.
3. **Phase 13: Smart Chat Engine** — Inline entity cards (ChampionProfile, ItemCard, TraitCard, AugmentCard), smart reply suggestions, cross-entity query routing, Coach mode enhancement.
4. **Phase 14: RAG 2.0 + Full Data Ingest** — Metadata filtering by entity type, heuristic reranking, streaming citations, ingest 252 augments + 59 champions + 45+ items + traits + systems + rolling odds into vector DB (target: 500+ chunks).

### Why This Matters

- **Knowledge Graph** is the foundation for "smart" — not just keyword matching, but understanding relationships between champions, items, traits, and augments
- **UI fixes** address real pain points: long messages stretch the container, CitationCards truncate important info, no responsive design
- **Smart Chat** turns flat text responses into structured, cross-linked entity cards that feel like a real TFT wiki
- **RAG 2.0** ensures the LLM has rich, well-categorized data to ground its answers

### Requirements

| Phase | REQ-IDs | Count |
|-------|---------|-------|
| 11 | KNOW-01..04 | 4 |
| 12 | UI-01..05 | 5 |
| 13 | SMART-01..05 | 5 |
| 14 | RAG2-01..05 | 5 |
| **Total** | | **19** |

### Key Files (Ingest Sources)

| Source File | Entities | Target Chunks |
|-------------|---------|--------------|
| `augments_full_user_verified.json` | 252 augments | ~180 |
| `traits_full_user_verified.json` | 30+ traits | ~35 |
| `items_effects_expanded_set17.json` | 45+ items | ~50 |
| `tft_set17_patch17_1_deep_pack_v4_user_verified.json` | 59 champions + systems | ~100 |
| `tft_set17_patch17_1_enhanced_pack.json` | 9 Space Gods | ~20 |
| `rolling_odds_user_verified.json` | rolling odds | ~10 |
| **Total** | | **≥ 500** |

---

## v1.3 Hardening & Polish — SHIPPED 2026-04-23

**Date:** 2026-04-23
**Phase:** Phase 10 (5 plans)
**Goal:** Fix UX issues and add polish features.

**Target features:**
- ✅ Session switch loading state (spinner) — HARD-01
- ✅ Frontend request timeout (60s) — HARD-02
- ✅ Pydantic validation bounds — HARD-03
- ✅ CompCard component integration — HARD-04
- ✅ Toast notification system — HARD-05

**Root causes fixed:**
- GPU status SyntaxError: `/health/gpu` → `/api/health/gpu` in `useGpuStatus.ts`
- PatchStatus CORS block: hardcoded URL → `/api/patch/status` via Vite proxy

**Required REQ-IDs:** HARD-01 through HARD-05 — **5/5 shipped**

---

## v1.2 MetaTFT Real-time Intelligence — SHIPPED 2026-04-23

**Date:** 2026-04-23
**Phase:** Phase 9 (3 plans)
**Goal:** Daily MetaTFT data refresh + CompCard frontend rendering.

**Target features:**
- ✅ MetaTFT scraper endpoint (`POST /api/ingest/metatft`) — META-01
- ✅ MetaTFT Markdown transformer — META-02
- ✅ Full Space Gods set data ingest (patch 17.1 + set overview) — META-03
- ✅ n8n daily MetaTFT refresh (12:00 noon) — META-04
- ✅ Frontend CompCard component — META-05

**Required REQ-IDs:** META-01 through META-05 — **5/5 shipped**

---

## v1.1 TFT Meta Mastery — SHIPPED 2026-04-22

**Date:** 2026-04-22
**Phase:** Phase 8 (4 plans)
**Goal:** Automated TFT meta intelligence — patch state in DB, n8n monitors Riot, auto-ingests patch notes + static data.

**Target features:**
- ✅ Patch state persisted in DB (not just file) — `patch_info` table
- ✅ Auto-scrape & ingest patch notes on new patch detection — `POST /api/ingest/patch-notes`
- ✅ n8n workflow activates and monitors patch changes — `patch_monitor.json` `active: true`
- ✅ Frontend displays patch version + staleness status — `PatchStatus` component

**Required REQ-IDs:** PATCH-01 through PATCH-05 — **5/5 shipped**

---

## v1.0 MVP — SHIPPED 2026-04-22

**Date:** 2026-04-22
**Phases:** 7 (1–7)
**Plans:** 22+
**Smoke test:** 60/60 PASS

### Accomplishments

1. **Local-first AI copilot** — Ollama + FastAPI + React with full streaming chat
2. **3-mode chat** — Normal (free chat), RAG (grounded + cited), Coach (tactical advice)
3. **RAG pipeline** — Hybrid search (HNSW semantic + GIN full-text), Obsidian ingest, citation display
4. **TFT patch 17.1 data** — 32 chunks ingested from official Riot patch page + CommunityDragon
5. **Production polish** — TTL-LRU cache, GPU monitoring, 20-question smoke test eval
6. **Automation ready** — n8n workflows + Bearer token auth + patch monitoring

### Tech Decisions

- qwen3:1.7b (chat) + qwen3-embedding:4b (embedding) for 12GB VRAM compatibility
- Riot CDN + patch page scraping as data source (CDN blocks automated access)
- Embedding dimensions truncated from 2560 to 1024 (HNSW index limit)

---

## Archive

| Milestone | File |
|-----------|------|
| v1.0 MVP | [.planning/milestones/v1.0-ROADMAP.md](.planning/milestones/v1.0-ROADMAP.md) |
| v1.0 Requirements | [.planning/milestones/v1.0-REQUIREMENTS.md](.planning/milestones/v1.0-REQUIREMENTS.md) |
| v1.1 TFT Meta Mastery | [.planning/milestones/v1.1-ROADMAP.md](.planning/milestones/v1.1-ROADMAP.md) |
| v1.1 Requirements | [.planning/milestones/v1.1-REQUIREMENTS.md](.planning/milestones/v1.1-REQUIREMENTS.md) |
