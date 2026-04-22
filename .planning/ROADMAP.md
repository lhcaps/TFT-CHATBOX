# ROADMAP: TFT Local Copilot

**Project:** TFT Local Copilot
**Created:** 2026-04-22
**Granularity:** standard
**Parallelization:** enabled (yolo mode)

---

## Milestones

- ✅ **v1.0 MVP** — Phases 1-7 (shipped 2026-04-22) — 60/60 smoke test PASS
- ✅ **v1.1 TFT Meta Mastery** — Phase 8 (shipped 2026-04-22) — PATCH-01..05 complete
- 📋 **v1.2 MetaTFT Real-time Intelligence** — Phase 9 (planning) — META-01..05

---

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-7) — SHIPPED 2026-04-22</summary>

- [x] Phase 1: Environment Setup (5/5 plans) — completed 2026-04-22
- [x] Phase 2: Backend Core (4/4 plans) — completed 2026-04-22
- [x] Phase 3: Frontend Chat (complete) — completed 2026-04-22
- [x] Phase 4: RAG Foundation (3/3 plans) — completed 2026-04-22
- [x] Phase 5: TFT Static Data (4/4 plans) — completed 2026-04-22
- [x] Phase 6: Automation (4/4 plans) — completed 2026-04-22
- [x] Phase 7: Polish & Smoke Test (4/4 plans) — completed 2026-04-22

**Smoke Test:** 60/60 PASS — 20 questions × 3 modes (Normal/RAG/Coach)

Full details: [.planning/milestones/v1.0-ROADMAP.md](.planning/milestones/v1.0-ROADMAP.md)

</details>

<details>
<summary>✅ v1.1 TFT Meta Mastery (Phase 8) — SHIPPED 2026-04-22</summary>

- [x] Phase 8: Patch Meta Mastery (4/4 plans) — shipped 2026-04-22
  - PATCH-01: patch_info table in DB ✅
  - PATCH-02: Backend patch status API ✅
  - PATCH-03: Auto-scrape patch notes API ✅
  - PATCH-04: n8n workflow activated ✅
  - PATCH-05: Frontend patch display ✅

**Details:** patch_state persisted in DB, patch notes auto-ingest via n8n, Discord notifications, frontend badge.

Full details: [.planning/milestones/v1.1-ROADMAP.md](.planning/milestones/v1.1-ROADMAP.md)

</details>

<details>
<summary>📋 v1.2 MetaTFT Real-time Intelligence (Phase 9) — planning</summary>

- [ ] Phase 9: MetaTFT Real-time Intelligence
  - META-01: MetaTFT scraper endpoint (`POST /api/ingest/metatft`)
  - META-02: MetaTFT data → Markdown transformer
  - META-03: Full Space Gods set data ingest (patch 17.1 + set overview)
  - META-04: n8n daily MetaTFT refresh (12:00 noon)
  - META-05: Frontend CompCard component

**Plans:** 3 plans

**Plan list:**
- [ ] 09-01-PLAN.md — MetaTFT Scraper + Backend Ingest Endpoint
- [ ] 09-02-PLAN.md — n8n Daily MetaTFT Trigger
- [ ] 09-03-PLAN.md — Frontend CompCard Component

**Canonical sources:**
- `https://www.metatft.com/comps` — comp tiers, winrates, carries, items
- `https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/teamfight-tactics-patch-17-1/`
- `https://teamfighttactics.leagueoflegends.com/en-us/set-overview/tft-set-17-space-gods/`

**No browser automation.** httpx + regex JSON extraction only.

Full details: [.planning/phases/09-metatft-intelligence/](.planning/phases/09-metatft-intelligence/)

</details>

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|--------------|--------|-----------|
| 1. Environment Setup | v1.0 | 5/5 | Complete | 2026-04-22 |
| 2. Backend Core | v1.0 | 4/4 | Complete | 2026-04-22 |
| 3. Frontend Chat | v1.0 | N/N | Complete | 2026-04-22 |
| 4. RAG Foundation | v1.0 | 3/3 | Complete | 2026-04-22 |
| 5. TFT Static Data | v1.0 | 4/4 | Complete | 2026-04-22 |
| 6. Automation | v1.0 | 4/4 | Complete | 2026-04-22 |
| 7. Polish & Smoke Test | v1.0 | 4/4 | Complete | 2026-04-22 |
| 8. Patch Meta Mastery | v1.1 | 4/4 | Complete | 2026-04-22 |
| 9. MetaTFT Intelligence | v1.2 | 0/N | Planning | — |

---

## v2 Requirements (Deferred)

> Note: PATCH-* requirements below are being addressed in **v1.1 TFT Meta Mastery**.

### RAG Enhancements
- RAG-08: Inline citation cards with hover/tap source snippets
- RAG-09: Streaming citation reveal alongside tokens
- RAG-10: Retrieval debug panel showing chunks, scores, sources
- RAG-11: Heuristic reranking: patch/season priority before cosine score
- RAG-12: Obsidian file watcher for real-time reactive sync

### Coach Mode Enhancements
- PROMPT-04: Visual line-of-play cards with icons (econ, tempo, board cap)
- PROMPT-05: Pivot fallback chain in every coach response
- PROMPT-06: In-game scenario presets (fast 8 roll, hyperoll open, 1-star holding)
- PROMPT-07: Coach persona customization (aggressive, safe, pivoting)

### Session Features
- SESS-01: Session auto-naming from first message
- SESS-02: Session search by keyword
- SESS-03: Session export as Markdown to Obsidian
- SESS-04: Cross-session memory from past conversations

### Model Upgrades
- MODEL-01: gemma3:12b for Coach mode, qwen3:8b for Normal/RAG
- MODEL-02: Query embedding cache (30-min TTL)

### Eval / Observability
- EVAL-01: Smoke test suite with scoring
- EVAL-02: Retrieval quality metrics (recall@K)
- EVAL-03: Structured logging for every request

---

## TFT Policy Compliance Notes

All phases comply with Riot TFT policy:
- **No real-time data:** Never build overlay, screen capture, or opponent scouting features
- **No game state reading:** Coach mode suggestions based on user's stated context only
- **Suggest, don't dictate:** Coach responses frame recommendations as options with trade-offs
- **Local-only:** All data stays on user's machine — no external API calls except Riot Data Dragon (static)
- **Unofficial tool:** Clearly disclaim no affiliation with Riot Games

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time opponent scouting / board scanning | Violates Riot TFT policy |
| In-game overlay or HUD | Violates TFT policy; dictates decisions |
| Automated "best action" button or macro | Removes player agency |
| Cloud API dependencies | Must remain fully local |
| Auth / user management | Single local user, no multi-user need |
| Non-Windows targets | MVP is Windows-only |
| WebSocket instead of SSE | SSE is sufficient for streaming |
| Redis or distributed cache | In-memory LRU sufficient for MVP |
| Cross-encoder reranking | Heuristic reranking is good enough for MVP |

---

## Archive

- [.planning/milestones/v1.0-ROADMAP.md](.planning/milestones/v1.0-ROADMAP.md) — Full v1.0 phase details
- [.planning/milestones/v1.0-REQUIREMENTS.md](.planning/milestones/v1.0-REQUIREMENTS.md) — All 35 v1 requirements (shipped)

---

*Last updated: 2026-04-22*
*Completed: v1.0 MVP + v1.1 TFT Meta Mastery — Phases 1-8 (shipped 2026-04-22)*
